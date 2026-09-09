using System;
using System.Runtime.InteropServices;

public static class ShellExecuteExHelper
{
    private const uint SEE_MASK_NOCLOSEPROCESS = 0x00000040;
    private const uint SEE_MASK_FLAG_NO_UI = 0x00000400;
    private const int SW_HIDE = 0;

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct SHELLEXECUTEINFO
    {
        public int cbSize;
        public uint fMask;
        public IntPtr hwnd;
        [MarshalAs(UnmanagedType.LPWStr)] public string lpVerb;
        [MarshalAs(UnmanagedType.LPWStr)] public string lpFile;
        [MarshalAs(UnmanagedType.LPWStr)] public string lpParameters;
        [MarshalAs(UnmanagedType.LPWStr)] public string lpDirectory;
        public int nShow;
        public IntPtr hInstApp;
        public IntPtr lpIDList;
        [MarshalAs(UnmanagedType.LPWStr)] public string lpClass;
        public IntPtr hkeyClass;
        public uint dwHotKey;
        public IntPtr hIconOrMonitor;
        public IntPtr hProcess;
    }

    [DllImport("shell32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool ShellExecuteExW(ref SHELLEXECUTEINFO lpExecInfo);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern uint GetProcessId(IntPtr hProcess);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool CloseHandle(IntPtr hObject);

    public static int Probe()
    {
        return 43;
    }

    public static int Run(string powershell)
    {
        SHELLEXECUTEINFO sei = new SHELLEXECUTEINFO();
        sei.cbSize = Marshal.SizeOf(typeof(SHELLEXECUTEINFO));
        sei.fMask = SEE_MASK_NOCLOSEPROCESS | SEE_MASK_FLAG_NO_UI;
        sei.lpVerb = "open";
        sei.lpFile = powershell;
        sei.lpParameters = "-NoLogo -NoProfile -NonInteractive -Command \"Start-Sleep -Seconds 30\"";
        sei.lpDirectory = null;
        sei.nShow = SW_HIDE;

        if (!ShellExecuteExW(ref sei))
        {
            int err = Marshal.GetLastWin32Error();
            return unchecked((int)(0xE3000000u | ((uint)err & 0x0000FFFFu)));
        }
        if (sei.hProcess == IntPtr.Zero)
            return unchecked((int)0xE4000000u);

        uint pid = GetProcessId(sei.hProcess);
        int pidErr = pid == 0 ? Marshal.GetLastWin32Error() : 0;
        CloseHandle(sei.hProcess);
        if (pid == 0)
            return unchecked((int)(0xE5000000u | ((uint)pidErr & 0x0000FFFFu)));
        return unchecked((int)(pid & 0x0FFFFFFFu));
    }
}
