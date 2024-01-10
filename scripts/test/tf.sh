#!/bin/sh
modules_to_analyze=

if [ "$#" -eq 0 ]; then
    echo "Running init, validate and plan for all modules under terraform/modules/"
    modules_to_analyze=$(find terraform/modules -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | tr '\n' ' ')
else
    echo "Running init, validate and plan for the following modules: $@"
    modules_to_analyze=$@
fi

for subfolder in $modules_to_analyze; do
        path="terraform/modules/$subfolder"
    if [ -d "$path" ]; then
        echo "provider \"aws\"" { >> $path/provider.tf
        echo "region=\"$AWS_REGION\"" >> $path/provider.tf
        echo } >> $path/provider.tf
        echo "Running init, valite and plan in: $path"
        terraform -chdir="$path" init
        terraform -chdir="$path" validate
        terraform -chdir="$path" plan -detailed-exitcode
    else
        echo "Error: $path is not a valid module directory."
        exit 1
    fi
done