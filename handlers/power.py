import subprocess, platform, asyncio
from time import time
from core.auth import restricted, power
import core.settings as settings_core
from core.settings import reload_settings
from utils.logger import logger
from telegram import Update
from telegram.ext import ContextTypes
from time import sleep as time_sleep

HibernationTask: asyncio.Task = None  

def power_off():
    """Power off the system."""
    reload_settings() 
    success, supported, error = False, True, None
    WAIT = settings_core.POWER_TIMER_WAIT
    if settings_core.VOID_POWER_TIMER:
        WAIT = 0  
    if platform.system() not in ["Windows", "Linux", "Darwin"]:
        supported = False
        logger.error("Unsupported operating system for power off.")
        return False, False, error
    
    if not settings_core.VOID_POWER_TIMER:
        logger.info(f"Shutting down in {WAIT} seconds.")

    try:
        if platform.system() == "Windows":
            subprocess.run(["shutdown", "/s", "/t", str(WAIT)], check=True)
        elif platform.system() == "Linux":
            subprocess.run(["shutdown", "-h", str(WAIT)], check=True)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["sudo", "shutdown", "-h", str(WAIT)], check=True)
        success = True
    except Exception as e:
        success = False
        logger.error(f"Failed to power off the system: {e}")
    return success, supported, error

def abort_shutdown():
    """Abort a scheduled shutdown or restart."""
    reload_settings()
    success, supported, error = False, True, None
    if platform.system() not in ["Windows", "Linux", "Darwin"]:
        supported = False
        logger.error("Unsupported operating system for aborting shutdown.")
        return success, supported, error
    
    try:
        if platform.system() == "Windows":
            subprocess.run(["shutdown", "/a"], check=True)
            success = True
        elif platform.system() == "Linux":
            subprocess.run(["shutdown", "-c"], check=True)
            success = True
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["sudo", "killall", "shutdown"], check=True)
            success = True
        else:
            success= False
            logger.error("Unsupported operating system for aborting shutdown.")
    except Exception as e:
        error = e
        success = False
        logger.error(f"Failed to abort the shutdown: {e}")
    return success, supported, error

def restart():
    """Restart the system."""
    reload_settings() 
    success, supported, error = False, True, None
    WAIT = settings_core.POWER_TIMER_WAIT
    if settings_core.VOID_POWER_TIMER:
        WAIT = 0  
    if platform.system() not in ["Windows", "Linux", "Darwin"]:
        supported = False
        logger.error("Unsupported operating system for restart.")
        return False, False, error
    
    if not settings_core.VOID_POWER_TIMER:
        logger.info(f"Restarting in {WAIT} seconds before")
    
    try:
        if platform.system() == "Windows":
            subprocess.run(["shutdown", "/r", "/t", str(WAIT)], check=True)
        elif platform.system() == "Linux":
            subprocess.run(["shutdown", "-r", str(WAIT)], check=True)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["sudo", "shutdown", "-r", str(WAIT)], check=True)
        success = True
    except Exception as e:
        success = False
        error = e
        logger.error(f"Failed to restart the system: {e}")
    return success, supported, error

def abort_restart():
    """Abort a scheduled restart."""
    return abort_shutdown()  # The same command is used to abort both shutdown and restart
    
def get_uptime():
    """Get the system uptime in seconds."""
    error = None
    if platform.system() not in ["Windows", "Linux", "Darwin"]:
        logger.error("Unsupported operating system for getting uptime.")
        return "Unsupported operating system", None
    try:
        if platform.system() == "Windows":
            output = subprocess.check_output("net stats srv", shell=True, text=True)
            for line in output.splitlines():
                if "Statistics since" in line:
                    uptime_str = line.split("Statistics since")[1].strip()
                    uptime_time = time.strptime(uptime_str, "%m/%d/%Y %I:%M:%S %p")
                    uptime_seconds = time.mktime(time.localtime()) - time.mktime(uptime_time)
                    return error, int(uptime_seconds)
        elif platform.system() == "Linux":
            with open("/proc/uptime", "r") as f:
                uptime_seconds = float(f.readline().split()[0])
                return error, int(uptime_seconds)
        elif platform.system() == "Darwin":  # macOS
            output = subprocess.check_output("sysctl -n kern.boottime", shell=True, text=True)
            boot_time_str = output.strip().split('=')[1].strip().split(',')[0]
            boot_time = time.strptime(boot_time_str, "%s")
            uptime_seconds = time.mktime(time.localtime()) - time.mktime(boot_time)
            return error, int(uptime_seconds)
        else:
            logger.error("Unsupported operating system for getting uptime.")
            return error, None
    except Exception as e:
        logger.error(f"Failed to get system uptime: {e}")
        return e, None

def sleep():
    """Put the system to sleep."""
    reload_settings() 
    success, supported, error = False, True, None
    if platform.system() not in ["Windows", "Linux", "Darwin"]:
        supported = False
        logger.error("Unsupported operating system for sleep.")
        return False, False, error

    try:
        if platform.system() == "Windows":
            subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], check=True)
        elif platform.system() == "Linux":
            subprocess.run(["systemctl", "suspend"], check=True)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["pmset", "sleepnow"], check=True)
        success = True
    except Exception as e:
        success = False
        error=e
        logger.error(f"Failed to put the system to sleep: {e}")
    return success, supported, error


async def hibernate_start():
    logger.info("Hibernate countdown started.")
    WAIT = settings_core.POWER_TIMER_WAIT
    try:
        await asyncio.sleep(WAIT)
        
        if platform.system() == "Windows":
            subprocess.run(["shutdown", "/h"], check=True)
        elif platform.system() == "Linux":
            subprocess.run(["systemctl", "hibernate"], check=True)
        return True
    except asyncio.CancelledError:
        logger.info("Hibernation task was cancelled successfully via code.")
        return False 
    except Exception as e:
        logger.error(f"Failed to hibernate the system: {e}")
        return e

async def hibernate(update: Update):
    """Hibernate the system."""
    reload_settings() 
    success, supported, error = False, True, None

    WAIT = settings_core.POWER_TIMER_WAIT
    if settings_core.VOID_POWER_TIMER:
        WAIT = 0  
    if platform.system() not in ["Windows", "Linux"]:
        # Note: Hibernate is not natively supported on macOS
        supported = False
        logger.error("Unsupported operating system for hibernate.")
        return False, False, error

    try:
       global HibernationTask
       if HibernationTask and not HibernationTask.done():
           HibernationTask.cancel()
           logger.info("Previous hibernation task cancelled.")
           await update.message.reply_text("Previous hibernation task cancelled. New hibernation task will be scheduled.")
       HibernationTask = asyncio.create_task(hibernate_start())
       success = True
    except Exception as e:
        success = False
        error = e
        logger.error(f"Failed to hibernate the system: {e}")
    return success, supported, error

async def AbortHibernate(update: Update):
    """Abort a scheduled hibernate."""
    global HibernationTask
    print(HibernationTask)
    if not HibernationTask or HibernationTask.done():
        await update.message.reply_text("No hibernation task is currently scheduled.")
        return
    HibernationTask.cancel()
    HibernationTask = None  # Reset the task after aborting
    await update.message.reply_text("Hibernation abort command sent. If a hibernation was scheduled, it will be aborted.")
    


class PowerManagerCmd:
    def __init__(self):
        self.power_off = power_off
        self.abort_shutdown = abort_shutdown
        self.restart = restart
        self.abort_restart = abort_restart
        self.abort_hibernate = AbortHibernate
        self.get_uptime = get_uptime
        self.sleep = sleep
        self.hibernate = hibernate

    @restricted
    @power
    async def power_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
        success, supported, error = power_off()
        if not supported:
            await update.message.reply_text("❌ Unsupported operating system for power off.\nSupported OS: Windows, Linux, macOS.")
        elif success:
            await update.message.reply_text("System is shutting down.")
        else:
            await update.message.reply_text(f"❌ Failed to power off the system: \n{error if error else 'Unknown error'}")
    @restricted
    @power
    async def abort_shutdown(update: Update, context: ContextTypes.DEFAULT_TYPE):
        success, supported, error = abort_shutdown()
        if not supported:
            await update.message.reply_text("❌ Unsupported operating system for aborting shutdown.\nSupported OS: Windows, Linux, macOS.")
        elif success:
            await update.message.reply_text("Shutdown aborted successfully.")
        else:
            await update.message.reply_text(f"❌ Failed to abort the shutdown: \n{error if error else 'Unknown error'}")
    @restricted
    @power
    async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
        success, supported, error = restart()
        if not supported:
            await update.message.reply_text("❌ Unsupported operating system for restart.\nSupported OS: Windows, Linux, macOS.")
        elif success:
            await update.message.reply_text("System is restarting.")
        else:
            await update.message.reply_text(f"❌ Failed to restart the system: \n{error if error else 'Unknown error'}")
    @restricted
    @power
    async def abort_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
        success, supported, error = abort_restart()
        if not supported:
            await update.message.reply_text("❌ Unsupported operating system for aborting restart.\nSupported OS: Windows, Linux, macOS.")
        elif success:
            await update.message.reply_text("Restart aborted successfully.")
        else:
            await update.message.reply_text(f"❌ Failed to abort the restart: \n{error if error else 'Unknown error'}")

    @restricted
    @power
    async def get_uptime(update: Update, context: ContextTypes.DEFAULT_TYPE):
        error, uptime_seconds = get_uptime()
        if uptime_seconds is None or error is not None:
            await update.message.reply_text(f"❌ Failed to get system uptime: \n{error if error else 'Unknown error'}")
        else:
            hours, remainder = divmod(uptime_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            await update.message.reply_text(f"System Uptime: {hours}h {minutes}m {seconds}s")
    
    @restricted
    @power
    async def sleep(update: Update, context: ContextTypes.DEFAULT_TYPE):
        success, supported, error = sleep()
        if not supported:
            await update.message.reply_text("❌ Unsupported operating system for sleep.\nSupported OS: Windows, Linux, macOS.")
        elif success:
            await update.message.reply_text("System is going to sleep.")
        else:
            await update.message.reply_text(f"❌ Failed to put the system to sleep: \n{error if error else 'Unknown error'}")
    
    @restricted
    @power
    async def hibernate(update: Update, context: ContextTypes.DEFAULT_TYPE):
        success, supported, error = await hibernate(update)
        global AbortHibernateFlag
        if not supported:
            await update.message.reply_text("❌ Unsupported operating system for hibernate.\nSupported OS: Windows, Linux.")
        elif success:
            await update.message.reply_text(f"System is hibernating in {settings_core.POWER_TIMER_WAIT} seconds.")
        elif not success:
            AbortHibernateFlag = False
            await update.message.reply_text("Hibernation aborted.")
        else:
            await update.message.reply_text(f"❌ Failed to hibernate the system: \n{error if error else 'Unknown error'}")

    @restricted
    @power
    async def abort_hibernate(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await AbortHibernate(update)

    @restricted
    @power
    async def lock_system(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lock the system."""
        reload_settings() 
        success, supported, error = False, True, None
        if platform.system() not in ["Windows", "Linux", "Darwin"]:
            supported = False
            logger.error("Unsupported operating system for lock.")
            await update.message.reply_text("❌ Unsupported operating system for lock.\nSupported OS: Windows, Linux, macOS.")
            return
        
        try:
            if platform.system() == "Windows":
                subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=True)
            elif platform.system() == "Linux":
                subprocess.run(["gnome-screensaver-command", "-l"], check=True)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession", "-suspend"], check=True)
            success = True
        except Exception as e:
            success = False
            error = e
            logger.error(f"Failed to lock the system: {e}")
        
        if success:
            await update.message.reply_text("System is locked.")
        else:
            await update.message.reply_text(f"❌ Failed to lock the system: \n{error if error else 'Unknown error'}")

    @restricted
    async def help_power_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        enabled = settings_core.POWER_MANAGEMENT

        commands_text = (
            "Available Power Commands:\n"
            "/power_off - Power off the system.\n"
            "/abort_shutdown - Abort a scheduled shutdown.\n"
            "/restart - Restart the system.\n"
            "/abort_restart - Abort a scheduled restart.\n"
            "/get_uptime - Get the system uptime.\n"
            "/sleep - Put the system to sleep.\n"
            "/hibernate - Hibernate the system (not supported on macOS).\n"
            "/abort_hibernate - Abort a scheduled hibernate. (supported only on Windows)\n"
            "/lock - Lock the system.\n"
        )

        disclaimer = (
            "\nDisclaimer: Power management commands are currently disabled in the .env file. "
            "Please enable <code>POWER_MANAGEMENT</code> in the .env file to use these commands."
        )

        help_text = commands_text + (disclaimer if not enabled else "")
        message = update.effective_message
        if message:
            await message.reply_text(help_text, parse_mode="HTML")
