import random
import uuid

def generate_otp():
    return str(random.randint(100000, 999999))

def upload_product_image_to(instance, filename):
    ext = filename.split('.')[-1]
    return f'product_images/{instance.store.owner.sqid}/{uuid.uuid4().hex}.{ext}'

def get_job_channel(domain, job_id):
    return f"{domain}-job-{job_id}"