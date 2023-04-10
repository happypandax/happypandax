# HappyPanda X Web Client

##### This is a web client using NextJS to connect to a HappyPanda X server.

[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/Pewpews/happypandax?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

> **Join the active development on gitter**

# Get Involved

Look for issues with the tag [`client rewrite`](https://github.com/happypandax/happypandax/issues) to see what needs to be worked on

# Setup

- Clone this repo
- Run `yarn install` at the root of the repo
- Build the CSS with `yarn run:client build:css`
- Start the client with `yarn start:client`

### Preparing a HPX server for client development

- Perform a backup of your HPX database
- If you're using a postgres database, docker is recommended to spin up a quick database
    Create Postgres containers:
    - `docker create -v /var/lib/postgresql/data --name hpx_data alpine`
    - `docker run -p 6998:5432 --name hpx_postgres -e POSTGRES_PASSWORD=hpx -d --restart unless-stopped --volumes-from hpx_data postgres`
    - Now you can  set `db.host: localhost`, `db.port: 6998`, `db.name: happypandax`, `db.user: postgres` and `db.password: hpx` 

- Set the following settings:
    - `core.debug` to `true`
    - `advanced.enable_cache` to `false`
    - If you're using a sqlite database:
        - `advanced.dev_db` to `true` (this is a hidden setting and can only be set in the config file), this will create a new sqlite database named `happypandax_dev.db` instead.

- Now restore your database backup to the new database, remember to check settings after the restore (because the previous settings might've been restored too)


You can use StoryBook for quick UI iteration: `yarn run:client storybook`