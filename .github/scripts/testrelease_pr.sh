#!/bin/bash

# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

# input testrelease version number, e.g. 1.1.0.1
version_number="$1"

branch_name="testrelease/rel-${version_number}"

# Create testrelease branch
echo "Creating new branch '$branch_name' from 'main'"
gh api -X POST /repos/solarwinds/apm-python/git/refs \
    --field ref="refs/heads/$branch_name" \
    --field sha="$(git rev-parse "origin/main")"

# Get SHA of current version.py at main
SHA_VERS=$(gh api /repos/solarwinds/apm-python/contents/solarwinds_apm/version.py?ref="main" --jq '.sha')

# Commit version.py with updated agent version
version_str=$(base64 <<< "__version__ = \"$version_number\"")
echo "Pushing new version.py to branch '$branch_name'"
gh api --method PUT /repos/solarwinds/apm-python/contents/solarwinds_apm/version.py \
    --field message="Update agent test version to $version_number" \
    --field content="$version_str" \
    --field encoding="base64" \
    --field branch="$branch_name" \
    --field sha="$SHA_VERS"

# Get SHA of current requirements-nodeps-beta.txt at main
SHA_REQ=$(gh api /repos/solarwinds/apm-python/contents/image/requirements-nodeps-beta.txt?ref="main" --jq '.sha')

# Commit beta image requirements with updated agent version
requirement_str=$(base64 <<< "solarwinds_apm==$version_number")
echo "Pushing new image/requirements to branch '$branch_name'"
gh api --method PUT /repos/solarwinds/apm-python/contents/image/requirements-nodeps-beta.txt \
    --field message="Update beta image's agent version to $version_number" \
    --field content="$requirement_str" \
    --field encoding="base64" \
    --field branch="$branch_name" \
    --field sha="$SHA_REQ"

# Open draft Pull Request for version bump
echo "Creating draft pull request"
gh pr create --draft --base "main" --head "$branch_name" \
    --title "solarwinds-apm $version_number" \
    --body "For testrelease of solarwinds-apm $version_number."