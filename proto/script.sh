#!/bin/bash

set -e

buf generate

mv ./web/dist/* ../