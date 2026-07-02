name: Bug report
description: Create a report to help us improve
title: "[BUG] "
labels: ["bug"]
body:
  - type: markdown
    attributes:
      value: |
        Thank you for reporting a bug! Please fill out the details below.
  - type: textarea
    id: description
    attributes:
      label: Description
      description: A clear and concise description of what the bug is.
      placeholder: Describe the problem...
    validations:
      required: true
  - type: textarea
    id: reproduction
    attributes:
      label: Steps to Reproduce
      description: How do we reproduce the behavior? Include job payloads, API calls, or worker configurations if applicable.
      placeholder: |
        1. Go to '...'
        2. Click on '....'
        3. Scroll down to '....'
        4. See error
    validations:
      required: true
  - type: textarea
    id: expected
    attributes:
      label: Expected Behavior
      description: A clear and concise description of what you expected to happen.
    validations:
      required: true
  - type: textarea
    id: environment
    attributes:
      label: Environment Info
      description: OS version, Docker Compose version, python/node versions, etc.
      placeholder: |
        - OS: Windows 11
        - Docker Compose: v2.20
        - Python: 3.11
    validations:
      required: true
