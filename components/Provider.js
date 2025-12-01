System.register(["react/jsx-runtime", "react-native", "tamagui", "@tamagui/toast", "./CurrentToast", "../tamagui.config"], function (exports_1, context_1) {
    "use strict";
    var jsx_runtime_1, react_native_1, tamagui_1, toast_1, CurrentToast_1, tamagui_config_1;
    var __moduleName = context_1 && context_1.id;
    function Provider({ children, ...rest }) {
        const colorScheme = react_native_1.useColorScheme();
        return (_jsx(tamagui_1.TamaguiProvider, { config: tamagui_config_1.config, defaultTheme: colorScheme === 'dark' ? 'dark' : 'light', ...rest, children: _jsxs(toast_1.ToastProvider, { swipeDirection: "horizontal", duration: 6000, native: [
                // uncomment the next line to do native toasts on mobile. NOTE: it'll require you making a dev build and won't work with Expo Go
                // 'mobile'
                ], children: [children, _jsx(CurrentToast_1.CurrentToast, {}), _jsx(toast_1.ToastViewport, { top: "$8", left: 0, right: 0 })] }) }));
    }
    exports_1("Provider", Provider);
    return {
        setters: [
            function (jsx_runtime_1_1) {
                jsx_runtime_1 = jsx_runtime_1_1;
            },
            function (react_native_1_1) {
                react_native_1 = react_native_1_1;
            },
            function (tamagui_1_1) {
                tamagui_1 = tamagui_1_1;
            },
            function (toast_1_1) {
                toast_1 = toast_1_1;
            },
            function (CurrentToast_1_1) {
                CurrentToast_1 = CurrentToast_1_1;
            },
            function (tamagui_config_1_1) {
                tamagui_config_1 = tamagui_config_1_1;
            }
        ],
        execute: function () {
        }
    };
});
