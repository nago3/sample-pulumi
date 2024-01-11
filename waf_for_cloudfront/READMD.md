# CloudFront - S3

## Attention

This code MUST work in `us-east-1` region.

## Command

### preset

```shell
$ pulumi config set env <env name>
$ pulumi config set owner <owner name>
```

### setup

```shell
$ pulumi up
```

## After work

Import Export stack data.

- Use JSON file to CloudFront_S3 directory.

```shell
$ pulumi stack export > stack.json
```
