#!/bin/bash
# The Argo CD install manifest binds ClusterRoles to the "argocd" namespace.
# Since we installed in "argocd-ricj", point the bindings there.
for crb in argocd-application-controller argocd-server argocd-applicationset-controller; do
  kubectl patch clusterrolebinding $crb --type='json' \
    -p='[{"op":"replace","path":"/subjects/0/namespace","value":"argocd-ricj"}]'
done
