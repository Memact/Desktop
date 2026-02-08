using System;
using System.Diagnostics;
using System.Runtime.InteropServices;

namespace Memact.Hooks
{
    public static class GlobalHooks
    {
        public static event Action? MouseUp;
        public static event Action? CapsDown;
        public static event Action? CapsUp;

        private static IntPtr _kb;
        private static IntPtr _mouse;

        public static void Install()
        {
            _kb = SetHook(13, KeyboardProc);
            _mouse = SetHook(14, MouseProc);
        }

        private static IntPtr SetHook(int id, HookProc proc)
        {
            using var p = Process.GetCurrentProcess();
            using var m = p.MainModule!;
            return SetWindowsHookEx(id, proc, GetModuleHandle(m.ModuleName), 0);
        }

        private static IntPtr KeyboardProc(int code, IntPtr w, IntPtr l)
        {
            if (code >= 0)
            {
                int vk = Marshal.ReadInt32(l);
                if (vk == 0x14)
                {
                    if ((int)w == 0x0100) CapsDown?.Invoke();
                    if ((int)w == 0x0101) CapsUp?.Invoke();
                }
            }
            return CallNextHookEx(_kb, code, w, l);
        }

        private static IntPtr MouseProc(int code, IntPtr w, IntPtr l)
        {
            if (code >= 0 && (int)w == 0x0202)
                MouseUp?.Invoke();

            return CallNextHookEx(_mouse, code, w, l);
        }

        private delegate IntPtr HookProc(int nCode, IntPtr wParam, IntPtr lParam);

        [DllImport("user32.dll")] static extern IntPtr SetWindowsHookEx(int id, HookProc proc, IntPtr mod, uint tid);
        [DllImport("user32.dll")] static extern IntPtr CallNextHookEx(IntPtr h, int c, IntPtr w, IntPtr l);
        [DllImport("kernel32.dll")] static extern IntPtr GetModuleHandle(string name);
    }
}
