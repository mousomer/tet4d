using System.IO;
using UnityEngine;

namespace Tet4D.UnityReplay.Tests
{
    internal static class TraceTestPaths
    {
        public static string BundleRoot()
        {
            return Path.GetFullPath(
                Path.Combine(Application.dataPath, "StreamingAssets", "tet4d_bundle")
            );
        }
    }
}
