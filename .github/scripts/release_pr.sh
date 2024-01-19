#!/bin/bash

# © 2024 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

# input release version number, e.g. 1.1.0
version_number="$1"

branch_name="release/rel-${version_number}"

# Create release branch
echo "Creating new branch '$branch_name' from 'main'"
gh api -X POST /repos/solarwinds/apm-python/git/refs \
    --field ref="refs/heads/$branch_name" \
    --field sha="$(git rev-parse "origin/main")"

# Get SHA of current version.py at main
SHA=$(gh api /repos/solarwinds/apm-python/contents/solarwinds_apm/version.py?ref="main" --jq '.sha')

# Commit version.py with updated agent version
echo "Pushing new version.py to branch '$branch_name'"
gh api --method PUT /repos/solarwinds/apm-python/contents/solarwinds_apm/version.py \
    --field message="Update agent version to $version_number" \
    --field content="__version__%20=%20'$version_number'" \
    --field branch="$branch_name" \
    --field sha="$SHA"

# Open draft Pull Request for version bump
echo "Creating draft pull request"
gh pr create --draft --base "main" --head "$branch_name" \
    --title "solarwinds-apm $version_number" \
    --body "For PyPI release of solarwinds-apm $version_number. See also CHANGELOG.md."