# Lambda

Super WIP test for semi-automated custom layer creation because I can't get opentelemetry-lambda Python archive creation to work!!!

## How-To

TODO streamline this

```
cd <path_to>/solarwinds-apm-python/lambda
docker run -it -v ${PWD}:/lambda --rm amazonlinux:2023 bash
cd lambda/python
yum install -y python3-devel python3-pip python3-setuptools
update-alternatives --install /usr/bin/python python /usr/bin/python3 1
pip install -r requirements.txt -t .
pip install -r requirements-nodeps.txt -t .
pip install -r requirements-testpypi.txt --extra-index-url https://test.pypi.org/simple/ -t .
exit

# Do this in <path_to>/solarwinds-apm-python/lambda,
# not inside the python dir
zip -r solarwinds-apm-lambda-layer.zip .
```