process.traceDeprecation = true;
const mf_config = require("@patternslib/dev/webpack/webpack.mf");
const path = require("path");
const package_json = require("./package.json");
const webpack_config =
    require("@patternslib/dev/webpack/webpack.config").config;

module.exports = () => {
    let config = {
        entry: {
            "ims.sso.min": path.resolve(__dirname, "resources/index"),
        },
    };

    config = webpack_config({
        config: config,
        package_json: package_json,
    });
    config.output.path = path.resolve(__dirname, "ims/sso/static/bundle");

    config.module.rules.push({
        test: /\.svg$/i,
        type: "asset/resource",
    });

    if (process.env.NODE_ENV === "development") {
        config.devServer.port = "8011";
        config.devServer.static.directory = __dirname;
    }

    // console.log(JSON.stringify(config, null, 4));

    return config;
};
