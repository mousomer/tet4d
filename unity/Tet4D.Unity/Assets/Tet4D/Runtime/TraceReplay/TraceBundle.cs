using System.Collections.Generic;
using Newtonsoft.Json.Linq;

namespace Tet4D.UnityReplay.TraceReplay
{
    public sealed class TraceBundle
    {
        public string RootPath { get; private set; }
        public TraceManifest Manifest { get; private set; }
        public JObject ConfigSnapshot { get; private set; }
        public JObject AuthorityIndex { get; private set; }
        public JObject SchemaIndex { get; private set; }

        public TraceBundle(
            string rootPath,
            TraceManifest manifest,
            JObject configSnapshot,
            JObject authorityIndex,
            JObject schemaIndex
        )
        {
            RootPath = rootPath;
            Manifest = manifest;
            ConfigSnapshot = configSnapshot;
            AuthorityIndex = authorityIndex;
            SchemaIndex = schemaIndex;
        }

        public List<string> TraceTypes()
        {
            return new List<string>(Manifest.CasesByTraceType.Keys);
        }

        public List<TraceCaseIndex> CasesForTraceType(string traceType)
        {
            List<TraceCaseIndex> cases;
            if (Manifest.CasesByTraceType.TryGetValue(traceType, out cases))
            {
                return cases;
            }

            return new List<TraceCaseIndex>();
        }
    }
}
