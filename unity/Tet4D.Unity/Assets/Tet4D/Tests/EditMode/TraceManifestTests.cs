using NUnit.Framework;
using Tet4D.UnityReplay.TraceReplay;

namespace Tet4D.UnityReplay.Tests
{
    public sealed class TraceManifestTests
    {
        [Test]
        public void ManifestLoadsAndExposesTraceGroups()
        {
            TraceBundle bundle = TraceLoader.LoadBundle(TraceTestPaths.BundleRoot());

            Assert.That(bundle.Manifest.BundleType, Is.EqualTo("tet4d_migration_bundle"));
            Assert.That(bundle.Manifest.BundleVersion, Is.EqualTo(1));
            Assert.That(bundle.Manifest.CasesByTraceType.ContainsKey("topology"), Is.True);
            Assert.That(bundle.Manifest.CasesByTraceType.ContainsKey("gameplay"), Is.True);
            Assert.That(bundle.Manifest.CasesByTraceType.ContainsKey("endgame"), Is.True);
            Assert.That(bundle.CasesForTraceType("topology").Count, Is.GreaterThan(0));
            Assert.That(bundle.CasesForTraceType("gameplay").Count, Is.GreaterThan(0));
            Assert.That(bundle.CasesForTraceType("endgame").Count, Is.GreaterThan(0));
        }
    }
}
