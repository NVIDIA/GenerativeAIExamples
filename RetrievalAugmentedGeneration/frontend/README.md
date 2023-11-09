# Customizing the frontend

This section chalks out steps needed for updating the static HTML and JavaScript based pages.

The Kaizen UI frame is stored in the folder [fronted_js/](frontend_js). To make modifications to this content, you will need an up-to-date version of NodeJS and NPM. You can find instructions on the install of those components in the [official NodeJS documentation](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm).

> **NOTE:** If you are using Ubuntu, do not use NodeJS from the Ubuntu repositories. It is too old to work with NextJS.

Once you have a working install of NodeJS, open a shell in the [fronted_js/](frontend_js) and run the following command:

```bash
npm install
```

This will install NextJS and all of the necesary Kaizen UI and React components into the [fronted_js/node_modules/](fronted_js/node_modules) folder.

The source code for the outer frame is in the [fronted_js/src/](fronted_js/src) directory. You can make modifications to this and run a development server to see your changes by running the following command:

```bash
npm run dev
```

> **NOTE:** The development server will not be able to run and mount the Gradio applications. Instead, you will see the outer frame mounted in itself with a 404 message. This is normal.

When your changes are complete, you can compile the NextJS code into static HTML and JavaScript with the following command:

```bash
npm run build
```

This will place the compiled static code in the [fronted_js/out/](fronted_js/out) directory. This must be copied in the the FastAPI static directory. However, be sure to remove the existing static content in FastAPI. Open a shell in this projects root folder and run the following commands:

```bash
rm -rf frontend/static/*
cp -rav frontend_js/out/* frontend/static/
```

The next time you launch the FastAPI server, it will now have your updated outer frame.