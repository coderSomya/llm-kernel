#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/device.h>
#include <asm/uaccess.h>

#define DEVICE_NAME "simple_dev"
#define CLASS_NAME  "simple_class"
#define BUFFER_SIZE 1024

static int major_number;
static struct class* simple_class = NULL;
static struct device* simple_device = NULL;
static char buffer[BUFFER_SIZE];
staticloff_t file_offset;

static ssize_t
simple_read(struct file *filp, char __user *buf, size_t count, loff_t *fpos)
{
	if (*fpos >= BUFFER_SIZE) {
		count = 0;
	} else {
		count = min(count, BUFFER_SIZE - *fpos);
		copy_to_user(buf, buffer + *fpos, count);
		*fpos += count;
	}
	return count;
}

static ssize_t
simple_write(struct file *filp, const char __user *buf, size_t count, loff_t *fpos)
{
	if (*fpos >= BUFFER_SIZE) {
		count = 0;
	} else {
		count = min(count, BUFFER_SIZE - *fpos);
		copy_from_user(buffer + *fpos, buf, count);
		*fpos += count;
	}
	return count;
}

static struct file_operations fops =
{
	.read = simple_read,
	.write = simple_write,
};

static int __init simple_init(void)
{
	major_number = register_chrdev(0, DEVICE_NAME, &fops);

	if (major_number < 0) {
		print_kernel_err("register_chrdev failed\n");
		return major_number;
	}

	simple_class = class_create(THIS_MODULE, CLASS_NAME);
	if (IS_ERR(simple_class)) {
		unregister_chrdev(major_number, DEVICE_NAME);
		print_kernel_err("class_create failed\n");
		return PTR_ERR(simple_class);
	}

	simple_device = device_create(simple_class, NULL, MKDEV(major_number, 0), NULL, DEVICE_NAME);
	if (IS_ERR(simple_device)) {
		class_destroy(simple_class);
		unregister_chrdev(major_number, DEVICE_NAME);
		print_kernel_err("device_create failed\n");
		return PTR_ERR(simple_device);
	}

	print_kernel_info("Module initialized successfully\n");
	return 0;
}

static void __exit simple_exit(void)
{
	device_destroy(simple_class, MKDEV(major_number, 0));
	class_destroy(simple_class);
	unregister_chrdev(major_number, DEVICE_NAME);

	print_kernel_info("Module removed successfully\n");
}

module_init(simple_init);
module_exit(simple_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Your Name");
MODULE_DESCRIPTION("Simple character device driver");