```c
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/device.h>
#include <linux/uaccess.h>

#define DEVICE_NAME "simple_dev"
#define CLASS_NAME  "simple_class"
#define BUFFER_SIZE 1024

static char buffer[BUFFER_SIZE];
static int major;
static struct cdev cdev_struct;
static struct class *class_ptr = NULL;
static struct device *device_ptr = NULL;

void simple_release(struct device *dev)
{
    cdev_del(&cdev_struct);
    kfree(buffer);
}

int simple_open(struct inode *inode, struct file *file)
{
    return single_open(file, NULL, NULL);
}

ssize_t simple_read(struct file *filp, char __user *buf, size_t count, loff_t *f_pos)
{
    if (*f_pos >= BUFFER_SIZE || count == 0) {
        return 0;
    }
    count = min(count, BUFFER_SIZE - *f_pos);
    if (copy_to_user(buf, &buffer[*f_pos], count)) {
        return -EFAULT;
    }
    *f_pos += count;
    return count;
}

ssize_t simple_write(struct file *filp, const char __user *buf, size_t count, loff_t *f_pos)
{
    if (*f_pos >= BUFFER_SIZE) {
        return 0;
    }
    count = min(count, BUFFER_SIZE - *f_pos);
    if (copy_from_user(&buffer[*f_pos], buf, count)) {
        return -EFAULT;
    }
    *f_pos += count;
    return count;
}

struct file_operations fops = {
    .owner = THIS_MODULE,
    .open = simple_open,
    .read = simple_read,
    .write = simple_write,
    .release = single_release,
};

int __init simple_init(void)
{
    int result;

    major = register_chrdev(0, DEVICE_NAME, &fops);
    if (major < 0) {
        return result;
    }

    class_ptr = class_create(THIS_MODULE, CLASS_NAME);
    if (IS_ERR(class_ptr)) {
        unregister_chrdev(major, DEVICE_NAME);
        return PTR_ERR(class_ptr);
    }

    device_ptr = device_create(class_ptr, NULL, MKDEV(major, 0), NULL, DEVICE_NAME);
    if (IS_ERR(device_ptr)) {
        class_destroy(class_ptr);
        unregister_chrdev(major, DEVICE_NAME);
        return PTR_ERR(device_ptr);
    }

    cdev_init(&cdev_struct, &fops);
    cdev_add(&cdev_struct, MKDEV(major, 0), 1);

    return 0;
}

void __exit simple_exit(void)
{
    cdev_del(&cdev_struct);
    device_destroy(class_ptr, MKDEV(major, 0));
    class_unregister(class_ptr);
    class_destroy(class_ptr);
    unregister_chrdev(major, DEVICE_NAME);
}

module_init(simple_init);
module_exit(simple_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Your Name");
MODULE_DESCRIPTION("Simple Character Device Driver");
```