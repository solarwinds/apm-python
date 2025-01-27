# To build one auto-instrumentation image for Python, please:
# - Ensure the packages are installed in the `/autoinstrumentation,{-musl}` directory. This is required as when instrumenting the pod,
#   one init container will be created to copy all the content in `/autoinstrumentation{,-musl}` directory to your app's container. Then
#   update the `PYTHONPATH` environment variable accordingly. To achieve this, you can mimic the one in `autoinstrumentation/python/Dockerfile`
#   by using multi-stage builds. In the first stage, install all the required packages in one custom directory with `pip install --target`.
#   Then in the second stage, copy the directory to `/autoinstrumentation{,-musl}`.
# - Ensure you have `opentelemetry-distro` and `opentelemetry-instrumentation` or your customized alternatives installed.
#   Those two packages are essential to Python auto-instrumentation.
# - Grant the necessary access to `/autoinstrumentation{,-musl}` directory. `chmod -R go+r /autoinstrumentation`
# - For auto-instrumentation by container injection, the Linux command cp is
#   used and must be availabe in the image.
#
# We install `nodeps` to cover all Python versions for Debian and Alpine
# for extension installations

FROM python:3.8 AS build-38
WORKDIR /operator-build
ADD requirements-nodeps.txt .
RUN mkdir workspace
RUN pip install --no-deps --target workspace -r requirements-nodeps.txt

FROM python:3.9 AS build-39
WORKDIR /operator-build
ADD requirements-nodeps.txt .
RUN mkdir workspace
RUN pip install --no-deps --target workspace -r requirements-nodeps.txt

FROM python:3.10 AS build-310
WORKDIR /operator-build
ADD requirements-nodeps.txt .
RUN mkdir workspace
RUN pip install --no-deps --target workspace -r requirements-nodeps.txt

FROM python:3.11 AS build-311
WORKDIR /operator-build
ADD requirements-nodeps.txt .
RUN mkdir workspace
RUN pip install --no-deps --target workspace -r requirements-nodeps.txt

FROM python:3.12 AS build-312
WORKDIR /operator-build
ADD requirements-nodeps.txt .
ADD requirements.txt .
RUN mkdir workspace
RUN pip install --no-deps --target workspace -r requirements-nodeps.txt
RUN pip install --target workspace -r requirements.txt


FROM python:3.8-alpine AS build-musl-38
WORKDIR /operator-build
ADD requirements-nodeps.txt .
RUN apk add g++ gcc python3-dev musl-dev linux-headers
RUN mkdir workspace
RUN pip install --no-deps --target workspace -r requirements-nodeps.txt

FROM python:3.9-alpine AS build-musl-39
WORKDIR /operator-build
ADD requirements-nodeps.txt .
RUN apk add g++ gcc python3-dev musl-dev linux-headers
RUN mkdir workspace
RUN pip install --no-deps --target workspace -r requirements-nodeps.txt

FROM python:3.10-alpine AS build-musl-310
WORKDIR /operator-build
ADD requirements-nodeps.txt .
RUN apk add g++ gcc python3-dev musl-dev linux-headers
RUN mkdir workspace
RUN pip install --no-deps --target workspace -r requirements-nodeps.txt

FROM python:3.11-alpine AS build-musl-311
WORKDIR /operator-build
ADD requirements-nodeps.txt .
RUN apk add g++ gcc python3-dev musl-dev linux-headers
RUN mkdir workspace
RUN pip install --no-deps --target workspace -r requirements-nodeps.txt

FROM python:3.12-alpine AS build-musl-312
WORKDIR /operator-build
ADD requirements-nodeps.txt .
ADD requirements.txt .
RUN apk add g++ gcc python3-dev musl-dev linux-headers
RUN mkdir workspace
RUN pip install --no-deps --target workspace -r requirements-nodeps.txt
RUN pip install --target workspace -r requirements.txt

FROM busybox

COPY --from=build-38 /operator-build/workspace /autoinstrumentation
COPY --from=build-39 /operator-build/workspace /autoinstrumentation
COPY --from=build-310 /operator-build/workspace /autoinstrumentation
COPY --from=build-311 /operator-build/workspace /autoinstrumentation
COPY --from=build-312 /operator-build/workspace /autoinstrumentation

COPY --from=build-musl-38 /operator-build/workspace /autoinstrumentation-musl
COPY --from=build-musl-39 /operator-build/workspace /autoinstrumentation-musl
COPY --from=build-musl-310 /operator-build/workspace /autoinstrumentation-musl
COPY --from=build-musl-311 /operator-build/workspace /autoinstrumentation-musl
COPY --from=build-musl-312 /operator-build/workspace /autoinstrumentation-musl

RUN chmod -R go+r /autoinstrumentation
RUN chmod -R go+r /autoinstrumentation-musl