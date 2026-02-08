using System;

namespace Memact.Hooks
{
    public class TriggerGate
    {
        private DateTime _last = DateTime.MinValue;
        private const int COOLDOWN = 700;

        public event Action? Trigger;

        public void OnMouseUp()
        {
            if ((DateTime.Now - _last).TotalMilliseconds < COOLDOWN)
                return;

            _last = DateTime.Now;
            Trigger?.Invoke();
        }
    }
}
