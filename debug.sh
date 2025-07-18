#!/bin/bash
docker run --rm -it --network host -v $(pwd):/app driver-eval /bin/bash
