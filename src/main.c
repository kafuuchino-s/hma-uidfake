// SPDX-License-Identifier: GPL-2.0
#include <linux/kernel.h>
#include <linux/module.h>

#include <linux/workqueue.h>

#include "uidfake.h"

struct static_key_false uidfake_debug_key;

/* Diagnostics switch themselves off, so a run that enabled them leaves nothing
 * behind. */
static void uidfake_debug_off(struct work_struct *work);
static DECLARE_DELAYED_WORK(uidfake_debug_work, uidfake_debug_off);

/* The parameter is a one-shot: it arms the key and the work item disarms it a
 * minute later. */
#ifdef UF_DEBUG_ALWAYS
static bool uidfake_debug = true;
#else
static bool uidfake_debug;
#endif
module_param_named(debug, uidfake_debug, bool, 0644);
MODULE_PARM_DESC(debug,
		 "log the isolated-child naming for 60 seconds after load");

static void uidfake_debug_off(struct work_struct *work)
{
	(void)work;
	if (static_key_enabled(&uidfake_debug_key)) {
		static_branch_disable(&uidfake_debug_key);
		pr_info("uidfake: diagnostics off\n");
	}
}

void uidfake_debug_init(bool on)
{
	if (!on)
		return;
	static_branch_enable(&uidfake_debug_key);
#ifdef UF_DEBUG_ALWAYS
	pr_info("uidfake: diagnostics on (compiled in, they never turn off)");
	return;
#else
	pr_info("uidfake: diagnostics on for 60 s\n");
	schedule_delayed_work(&uidfake_debug_work, 60UL * HZ);
#endif
}

static int __init uidfake_init(void)
{
	int rc = uidfake_resolver_init();

	if (rc)
		return rc;
	rc = policy_init();
	if (rc)
		return rc;
	rc = netlink_init();
	if (rc)
		goto free_policy;
	rc = hooks_install();
	if (rc <= 0) {
		pr_err("uidfake: initial hook preparation failed: %d\n", rc);
		rc = rc < 0 ? rc : -EIO;
		goto close_netlink;
	}
	uidfake_debug_init(uidfake_debug);
	pr_info("uidfake: ready (native=4 compat=4 LSM=1)\n");
	return 0;

close_netlink:
	/* The 4.19 installer returns an error only before callback publication. */
	netlink_exit();
free_policy:
	policy_free();
	return rc;
}

static void __exit uidfake_exit(void)
{
	cancel_delayed_work_sync(&uidfake_debug_work);
	netlink_exit();
	hooks_remove();
	policy_free();
	pr_info("uidfake: unloaded\n");
}

module_init(uidfake_init);
module_exit(uidfake_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("local");
MODULE_DESCRIPTION(
	"uidfake - kernel-side uid existence guard (netlink-injected policy)");
