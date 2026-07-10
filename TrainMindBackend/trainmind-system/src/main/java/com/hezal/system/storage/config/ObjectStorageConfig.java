package com.hezal.system.storage.config;

import java.net.URI;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.S3Configuration;

/**
 * 对象存储客户端配置。
 *
 * @author trainmind
 */
@Configuration
@EnableConfigurationProperties(ObjectStorageProperties.class)
@ConditionalOnProperty(prefix = "trainmind.storage", name = "enabled", havingValue = "true", matchIfMissing = true)
public class ObjectStorageConfig
{
    @Bean
    public S3Client s3Client(ObjectStorageProperties properties)
    {
        // SeaweedFS 本地 S3 端点要求 path-style access。
        S3Configuration serviceConfiguration = S3Configuration.builder()
                .pathStyleAccessEnabled(properties.isPathStyleAccess())
                .build();

        return S3Client.builder()
                .endpointOverride(URI.create(properties.getEndpoint()))
                .region(Region.of(properties.getRegion()))
                .credentialsProvider(StaticCredentialsProvider.create(
                        AwsBasicCredentials.create(properties.getAccessKey(), properties.getSecretKey())))
                .serviceConfiguration(serviceConfiguration)
                .build();
    }
}
