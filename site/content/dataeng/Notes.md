---
title: "Notes"
date: 2020-04-10T10:37:50-06:00
weight: 35
---

_Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: CC-BY-SA-4.0_

While we try to use best practices in this workshop, we made a couple of concessions to simplicity.

* Rather than using Secrets Manager, we stored the DocumentDB credentials as attributes in CloudMap.  This should never be done in production, but there is not a clean programmatic way to generate secrets.
* The permissions granted to Cloud9 and other resources could be more narrowly scoped.
