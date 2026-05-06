using NUnit.Framework;
using Tet4D.UnityReplay.TraceReplay;

namespace Tet4D.UnityReplay.Tests
{
    public sealed class BundleAuthorityTests
    {
        [Test]
        public void BundleRemainsExplicitlyNonAuthoritative()
        {
            TraceBundle bundle = TraceLoader.LoadBundle(TraceTestPaths.BundleRoot());

            Assert.That(bundle.Manifest.PythonSemanticOracle, Is.True);
            Assert.That(bundle.Manifest.ExportedBundleIsAuthority, Is.False);
        }
    }
}
