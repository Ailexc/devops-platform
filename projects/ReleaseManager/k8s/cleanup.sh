#!/bin/bash
echo ">>> 删除 kind 集群..."
kind delete cluster --name release-demo
echo "集群已删除"