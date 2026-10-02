# Source provenance / adapter boundaries

`source/FRONTEND_PROVENANCE.json`: every extraction original file,target,declaration name/line/mode. Function/interface bodies verbatim AST get Text; imports pruned/rewritten; only Dispatch,History,YardBrain retained. Shared components only trainColor,Panel,Badge,Network,Diagram,TrainDrawer; PageProps/PageTitle splitout. No other business pages hidden in mixed source files. Sourcecode includes all actual handlers/tooltips/formulas.

`source/BACKEND_PROVENANCE.json`: original file+SHA256 andmode. Simulator/scheduler/quality/ato/history/reports/yard maintain original math; Simulator DATA path adaptedtobundle/data and missing file generator path. API extractedrequiredhandlersplussettings/injection/reset support; resource allowed module only yard. ResourcePlanning explicit yard-onlyadapter keeps original response/calculation/apply/version/log behaviour. Fulloriginalresourcesmanagerdependsfleet/maintenance, so blindlycopyingitwouldforceunnecessarymodules; thisadapter avoids that.

Hostmain pre serves reference global session/live/lang/drawer behaviour but nav and routes only3;root redirect changed to/dispatch. Optional CSS isolated-page rulesremovedwithoutrestylingkeptpages. package-lockcopied, npm scripts limited to reference host; ViteHTTP/WSproxy8001,port5175 and external pages dependency resolution adapted. Original project remains separate.

Fulloriginaldatasetscopiedexceptresource_scenarios selecting seed/provenance/yard. No resource value renamed or regenerated. Stationenrichedinventoryisadditionalfile; original stations.json copiedverbatim. Datainventoryrecordsoriginalresourcefilehash/excludedsections. All captured runtime files labelled captured, never used as replacement math.

## Excluded intentionally

Overview,Traffic,Incidents page,TrainAdvisory page,Analytics,LocomotiveBrain,MaintenanceBrain,Settingspage; originalDockerdeploymentand11-pageentry; fleet.py,maintenance.py and their scenarios; unused SpeedChart/TrainTable; unrelatedtests/assets. ServerATO/core incidents/config retained only when required for tick,history/qualityorfixturehostsupport. Capture tool Playwright and verification are tooling, not new product features.

`CHECKSUMS.json` records deliverable source/data/docs/assets hashes (excluding runtime install/build directories). Verification confirms exact copy files againstoriginalSHAanddatasetjoinconsistency. A screenshot is functional reference, notmandatorydesign.
