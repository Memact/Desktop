using System.Collections.Generic;
using System.Linq;

namespace Memact.Core
{
    public class FrameBuffer
    {
        private readonly LinkedList<ActionFrame> _frames = new();
        private const int MAX = 25;

        public void Add(ActionFrame f)
        {
            _frames.AddLast(f);
            if (_frames.Count > MAX)
                _frames.RemoveFirst();
        }

        public ActionFrame? Best()
        {
            return _frames.OrderByDescending(x => x.Confidence).FirstOrDefault();
        }

        public void Remove(ActionFrame f) => _frames.Remove(f);

        public bool Empty => _frames.Count == 0;

        public IEnumerable<ActionFrame> All() => _frames;
    }
}
