using System;

namespace Memact.Hooks
{
    public class CapsRecall
    {
        private DateTime _down;
        private const int HOLD = 400;

        public event Action? Recall;

        public void Down() => _down = DateTime.Now;

        public void Up()
        {
            if ((DateTime.Now - _down).TotalMilliseconds >= HOLD)
                Recall?.Invoke();
        }
    }
}
