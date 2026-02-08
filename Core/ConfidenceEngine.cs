using System;

namespace Memact.Core
{
    public static class ConfidenceEngine
    {
        public static void Update(ActionFrame f, bool success)
        {
            if (success) f.Confidence += 0.15;
            else f.Confidence -= 0.25;

            f.Confidence = Math.Clamp(f.Confidence, 0.0, 1.0);
            f.Attempts++;
        }

        public static bool ShouldPrune(ActionFrame f)
        {
            var age = (DateTime.Now - f.Timestamp).TotalSeconds;
            f.Confidence -= age * 0.005;

            return f.Confidence <= 0.1 || age > 60 || f.Attempts > 2;
        }
    }
}
