System.register(["jotai"], function (exports_1, context_1) {
    "use strict";
    var jotai_1, birthDataAtom, activeFrameworkAtom, agentOutputsAtom, messagesAtom, healthMetricsAtom, journalEntriesAtom;
    var __moduleName = context_1 && context_1.id;
    return {
        setters: [
            function (jotai_1_1) {
                jotai_1 = jotai_1_1;
            }
        ],
        execute: function () {
            /**
             * Global state atoms for the app
             */
            // Birth data
            exports_1("birthDataAtom", birthDataAtom = jotai_1.atom(null));
            // Current active framework
            exports_1("activeFrameworkAtom", activeFrameworkAtom = jotai_1.atom('human-design'));
            // Agent outputs cache
            exports_1("agentOutputsAtom", agentOutputsAtom = jotai_1.atom({}));
            exports_1("messagesAtom", messagesAtom = jotai_1.atom([]));
            // Health metrics (from HealthKit)
            exports_1("healthMetricsAtom", healthMetricsAtom = jotai_1.atom({}));
            // Journal entries
            exports_1("journalEntriesAtom", journalEntriesAtom = jotai_1.atom([]));
        }
    };
});
