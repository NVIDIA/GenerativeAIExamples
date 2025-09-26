#!/bin/bash
set -eo pipefail

if [ "$MYSQL_ROOT_PASSWORD" ] && [ -z "$MYSQL_USER" ] && [ -z "$MYSQL_PASSWORD" ]; then
	echo >&2 'Healthcheck error: cannot determine root password (and MYSQL_USER and MYSQL_PASSWORD were not set)'
	exit 0
fi

host="$(hostname --ip-address || echo '127.0.0.1')"
user="${MYSQL_USER:-root}"
export MYSQL_PWD="${MYSQL_PASSWORD:-$MYSQL_ROOT_PASSWORD}"

args=(
	# force mysql to not use the local "mysqld.sock" (test "external" connectivity)
	-h"$host"
	-u"$user"
	--silent
)

STATUS=0
if command -v mysqladmin &> /dev/null; then
	if mysqladmin "${args[@]}" ping > /dev/null; then
		database_check=$(mysql -u$user -D oai_db --silent -e "SELECT * FROM AuthenticationSubscription;")
		if [[ -z $database_check ]]; then
			echo "Healthcheck error: oai_db not populated"
			STATUS=1
		fi
		STATUS=0
	else
		echo "Healthcheck error: Mysql port inactive"
		STATUS=1
	fi
else
	if select="$(echo 'SELECT 1' | mysql "${args[@]}")" && [ "$select" = '1' ]; then
		database_check=$(mysql -u$user -D oai_db --silent -e "SELECT * FROM AuthenticationSubscription;")
		if [[ -z $database_check ]]; then
			echo "Healthcheck error: oai_db not populated"
			STATUS=1
		fi
		STATUS=0
	else
		echo "Healthcheck error: Mysql port inactive"
		STATUS=1
	fi
fi
exit $STATUS
