System.register(["@tamagui/config/v4", "tamagui"], function (exports_1, context_1) {
    "use strict";
    var v4_1, tamagui_1, config;
    var __moduleName = context_1 && context_1.id;
    return {
        setters: [
            function (v4_1_1) {
                v4_1 = v4_1_1;
            },
            function (tamagui_1_1) {
                tamagui_1 = tamagui_1_1;
            }
        ],
        execute: function () {
            exports_1("config", config = tamagui_1.createTamagui(v4_1.defaultConfig));
            exports_1("default", config);
        }
    };
});
