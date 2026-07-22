#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:18080}"
PASSWORD="${STUDENT_ACCEPTANCE_PASSWORD:-admin123}"

json_value() {
  local expression="$1"
  node -e "const fs=require('fs');const x=JSON.parse(fs.readFileSync(0,'utf8'));const v=($expression);process.stdout.write(v == null ? '' : String(v))"
}

login() {
  local username="$1" captcha uuid code response token
  captcha="$(curl -fsS "$BASE_URL/captchaImage")"
  uuid="$(printf '%s' "$captcha" | sed -n 's/.*"uuid":"\([^"]*\)".*/\1/p')"
  code="$(redis-cli get "captcha_codes:$uuid" | tr -d '"')"
  response="$(curl -fsS -H 'Content-Type: application/json' \
    -d "{\"username\":\"$username\",\"password\":\"$PASSWORD\",\"code\":\"$code\",\"uuid\":\"$uuid\"}" \
    "$BASE_URL/login")"
  token="$(printf '%s' "$response" | json_value 'x.token')"
  test -n "$token" || { echo "FAIL login $username"; exit 1; }
  printf '%s' "$token"
}

get_json() {
  local token="$1" path="$2"
  curl -fsS -H "Authorization: Bearer $token" "$BASE_URL$path"
}

post_json() {
  local token="$1" path="$2" body="$3"
  curl -fsS -H "Authorization: Bearer $token" -H 'Content-Type: application/json' \
    -d "$body" "$BASE_URL$path"
}

assert_json() {
  local label="$1" json="$2" expression="$3"
  if printf '%s' "$json" | node -e "const fs=require('fs');const x=JSON.parse(fs.readFileSync(0,'utf8'));if(!($expression))process.exit(1)"
  then echo "PASS $label"
  else echo "FAIL $label"; exit 1
  fi
}

token_a="$(login student_accept_a)"
token_b="$(login student_accept_b)"

info_a="$(get_json "$token_a" /getInfo)"
assert_json "student role registered" "$info_a" "x.roles.includes('student')"

courses_a="$(get_json "$token_a" /student/courses)"
assert_json "multi-course and status matrix" "$courses_a" \
  "x.data.filter(c=>c.availability==='available').length===2 && x.data.some(c=>c.availability==='content_preparing') && x.data.some(c=>c.availability==='expired')"

tenant_escape="$(get_json "$token_a" /student/courses/9199)"
assert_json "cross-tenant course denied" "$tenant_escape" "x.code===500"

activity_path="/student/courses/1/activities"
post_json "$token_a" "$activity_path" '{"activityType":"course_view","targetId":1}' >/dev/null
post_json "$token_a" "$activity_path" '{"activityType":"course_view","targetId":1}' >/dev/null
activities="$(get_json "$token_a" "$activity_path")"
assert_json "activity visible to owner" "$activities" \
  "x.data.some(a=>a.activityType==='course_view' && a.targetId===1)"

outline="$(get_json "$token_a" /student/courses/1/outline)"
document_id="$(printf '%s' "$outline" | json_value 'x.data.modules.flatMap(m=>m.documents)[0]?.documentId')"
test -n "$document_id" || { echo 'FAIL published document fixture'; exit 1; }
download_status="$(curl -sS -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $token_a" \
  "$BASE_URL/student/courses/1/documents/$document_id/download")"
test "$download_status" = "403" && echo "PASS download policy enforced" || { echo "FAIL download policy enforced"; exit 1; }

session_response="$(post_json "$token_a" /student/courses/1/chat/sessions '{}')"
session_id="$(printf '%s' "$session_response" | json_value 'x.data.id')"
answer="$(post_json "$token_a" "/student/courses/1/chat/sessions/$session_id/messages" '{"question":"请说明本课程的主要内容"}')"
assert_json "AI outage degrades without losing message" "$answer" "x.data.status==='service_unavailable'"

foreign_session="$(get_json "$token_b" "/student/courses/1/chat/sessions/$session_id")"
assert_json "foreign session denied" "$foreign_session" "x.code===500"

foreign_course="$(get_json "$token_b" /student/courses/9101)"
assert_json "unassigned course denied" "$foreign_course" "x.code===500"

echo 'Student MVP smoke test completed.'
