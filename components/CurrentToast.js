System.register(["react/jsx-runtime", "@tamagui/toast", "tamagui"], function (exports_1, context_1) {
    "use strict";
    var jsx_runtime_1, toast_1, tamagui_1;
    var __moduleName = context_1 && context_1.id;
    function CurrentToast() {
        const currentToast = toast_1.useToastState();
        if (!currentToast || currentToast.isHandledNatively)
            return null;
        return (_jsx(toast_1.Toast, { duration: currentToast.duration, viewportName: currentToast.viewportName, enterStyle: { opacity: 0, scale: 0.5, y: -25 }, exitStyle: { opacity: 0, scale: 1, y: -20 }, y: tamagui_1.isWeb ? '$12' : 0, theme: "accent", rounded: "$6", animation: "quick", children: _jsxs(tamagui_1.YStack, { items: "center", p: "$2", gap: "$2", children: [_jsx(toast_1.Toast.Title, { fontWeight: "bold", children: currentToast.title }), !!currentToast.message && (_jsx(toast_1.Toast.Description, { children: currentToast.message }))] }) }, currentToast.id));
    }
    exports_1("CurrentToast", CurrentToast);
    function ToastControl() {
        const toast = toast_1.useToastController();
        return (_jsxs(tamagui_1.YStack, { gap: "$2", items: "center", children: [_jsx(tamagui_1.H4, { children: "Toast demo" }), _jsxs(tamagui_1.XStack, { gap: "$2", justify: "center", children: [_jsx(tamagui_1.Button, { onPress: () => {
                                toast.show('Successfully saved!', {
                                    message: "Don't worry, we've got your data.",
                                });
                            }, children: "Show" }), _jsx(tamagui_1.Button, { onPress: () => {
                                toast.hide();
                            }, children: "Hide" })] })] }));
    }
    exports_1("ToastControl", ToastControl);
    return {
        setters: [
            function (jsx_runtime_1_1) {
                jsx_runtime_1 = jsx_runtime_1_1;
            },
            function (toast_1_1) {
                toast_1 = toast_1_1;
            },
            function (tamagui_1_1) {
                tamagui_1 = tamagui_1_1;
            }
        ],
        execute: function () {
        }
    };
});
