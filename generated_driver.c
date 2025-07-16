#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/device.h>
#include <linux/uaccess.h>
#include <asm/ioctl.h>

#define CLASS_NAME "simple_char_dev"
#define DEVICE_NAME "simple_dev"
#define BUFFER_SIZE 1024

static int major_number;
static struct class *dev_class = NULL;
static struct device *dev_device = NULL;
static char buffer[BUFFER_SIZE];
staticloff_t file_offset;

static ssize_t simple_read(struct file *, char __user *, size_t, loff_t *);
static ssize_t simple_write(struct file *, const char __user *, size_t, loff_t *);

static struct file_operations fops = {
	.read = simple_read,
	.write = simple_write
};

static int __init simple_char_dev_init(void) {
	major_number = register_chrdev(0, DEVICE_NAME, &fops);
	if (major_number < 0) {
		return major_number;
	}

	dev_class = class_create(THIS_MODULE, CLASS_NAME);
	if (IS_ERR(dev_class)) {
		unregister_chrdev(major_number, DEVICE_NAME);
		return PTR_ERR(dev_class);
	}

	dev_device = device_create(dev_class, NULL, MKDEV(major_number, 0), NULL, DEVICE_NAME);
	if (IS_ERR(dev_device)) {
	.class_destroy(dev_class);
		unregister_chrdev(major_number, DEVICE_NAME);
		return PTR_ERR(dev_device);
	}

	printk(KERN_INFO "Simple character device loaded\n");
	return 0;
}

static void __exit simple_char_dev_exit(void) {
	device_destroy(dev_class, MKDEV(major_number, 0));
	class_destroy(dev_class);
	unregister_chrdev(major_number, DEVICE_NAME);
	printk(KERN_INFO "Simple character device unloaded\n");
}

static ssize_t simple_read(struct file *filp, char __user *buf, size_t count, loff_t *f_pos) {
	if (*f_pos >= BUFFER_SIZE)
		return 0;

	size_t len = BUFFER_SIZE - *f_pos;
	if (copy_to_user(buf, buffer + *f_pos, len))
		return -EFAULT;

	*f_pos += len;
	return len;
}

static ssize_t simple_write(struct file *filp, const char __user *buf, size_t count, loff_t *f_pos) {
	if (*f_pos >= BUFFER_SIZE)
		return 0;

	size_t len = BUFFER_SIZE - *f_pos;
	if (copy_from_user(buffer + *f_pos, buf, len))
		return -EFAULT;

	*f_pos += len;
	return len;
}

module_init(simple_char_dev_init);
module_exit(simple_char_dev_exit);

MODULE_LICENSE("GPL");