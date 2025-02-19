#!/bin/bash

# Run database migrations
psql $DATABASE_URL -f src/db/schema.sql 