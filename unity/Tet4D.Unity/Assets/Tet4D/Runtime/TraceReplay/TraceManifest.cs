using System.Collections.Generic;
using Newtonsoft.Json.Linq;

namespace Tet4D.UnityReplay.TraceReplay
{
    public sealed class TraceManifest
    {
        public string BundleType { get; private set; }
        public int BundleVersion { get; private set; }
        public bool ExportedBundleIsAuthority { get; private set; }
        public bool PythonSemanticOracle { get; private set; }
        public string ConfigCombinedDigest { get; private set; }
        public JObject RawObject { get; private set; }
        public Dictionary<string, List<TraceCaseIndex>> CasesByTraceType { get; private set; }

        public static TraceManifest FromJson(string jsonText)
        {
            JObject root = TraceJson.ParseObject(jsonText);
            TraceManifest manifest = new TraceManifest();
            manifest.RawObject = root;
            manifest.BundleType = TraceJson.GetString(root, "bundle_type");
            manifest.BundleVersion = TraceJson.GetInt(root, "bundle_version");
            manifest.ExportedBundleIsAuthority = TraceJson.GetBool(
                root,
                "authority.exported_bundle_is_authority"
            );
            manifest.PythonSemanticOracle = TraceJson.GetBool(
                root,
                "authority.python_semantic_oracle"
            );
            manifest.ConfigCombinedDigest = TraceJson.GetString(
                root,
                "config.combined_digest"
            );
            manifest.CasesByTraceType = new Dictionary<string, List<TraceCaseIndex>>();

            JObject tracesObject = TraceJson.GetObject(root, "traces");
            if (tracesObject == null)
            {
                return manifest;
            }

            foreach (JProperty property in tracesObject.Properties())
            {
                JArray cases = property.Value as JArray;
                List<TraceCaseIndex> indexes = new List<TraceCaseIndex>();
                if (cases != null)
                {
                    foreach (JToken token in cases)
                    {
                        indexes.Add(TraceCaseIndex.FromToken(property.Name, token));
                    }
                }

                manifest.CasesByTraceType[property.Name] = indexes;
            }

            return manifest;
        }
    }
}
