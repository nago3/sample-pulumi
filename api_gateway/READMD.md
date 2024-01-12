# CloudFront - S3

## Attention

API Gateway NOT in `us-east-1`, so if you need to use other region,
set Domain and certificate manually.

## command

### preset

```shell
$ pulumi config set env <env name>
$ pulumi config set owner <owner name>
$ pulumi config set lambda_function_name <lambda_function name>
```

### setup

```shell
$ pulumi up
```
