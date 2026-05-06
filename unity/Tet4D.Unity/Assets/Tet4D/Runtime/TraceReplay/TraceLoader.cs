using System;
using System.IO;
using Newtonsoft.Json.Linq;
using UnityEngine;

namespace Tet4D.UnityReplay.TraceReplay
{
    public static class TraceLoader
    {
        public static string DefaultBundleRoot()
        {
            return Path.Combine(Application.streamingAssetsPath, "tet4d_bundle");
        }

        public static TraceBundle LoadBundle(string bundleRoot)
        {
            if (!Directory.Exists(bundleRoot))
            {
                throw new DirectoryNotFoundException("Bundle root missing: " + bundleRoot);
            }

            string manifestPath = Path.Combine(bundleRoot, "manifest.json");
            string configPath = Path.Combine(bundleRoot, "config", "tet4d_config_bundle.json");
            string docsPath = Path.Combine(bundleRoot, "docs", "authority_index.json");
            string schemaPath = Path.Combine(bundleRoot, "schemas", "schema_index.json");

            TraceManifest manifest = TraceManifest.FromJson(File.ReadAllText(manifestPath));
            if (manifest.ExportedBundleIsAuthority)
            {
                throw new InvalidOperationException(
                    "Bundle authority flag is invalid for replay-only mode."
                );
            }

            JObject config = TraceJson.ParseObject(File.ReadAllText(configPath));
            JObject docs = TraceJson.ParseObject(File.ReadAllText(docsPath));
            JObject schema = TraceJson.ParseObject(File.ReadAllText(schemaPath));
            return new TraceBundle(bundleRoot, manifest, config, docs, schema);
        }

        public static TraceDocument LoadCaseDocument(TraceBundle bundle, TraceCaseIndex caseIndex)
        {
            string relativePath = caseIndex.RelativePath.Replace('/', Path.DirectorySeparatorChar);
            string absolutePath = Path.Combine(bundle.RootPath, relativePath);
            if (!File.Exists(absolutePath))
            {
                throw new FileNotFoundException("Trace case missing: " + absolutePath);
            }

            return TraceDocument.FromJson(File.ReadAllText(absolutePath));
        }
    }
}
