import os
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def generate_demo_site(business_name: str, category: str) -> str:
    """
    Generate a professional demo website for a business.
    
    Args:
        business_name: Name of the business
        category: Business category (dentist, gym, salon, etc.)
    
    Returns:
        URL path to the generated demo site
    """
    # Sanitize name for URL
    safe_name = re.sub(r'[^a-z0-9]', '-', business_name.lower())
    safe_name = re.sub(r'-+', '-', safe_name).strip('-')
    filename = f"{safe_name}-demo.html"
    filepath = os.path.join("demo_sites", filename)
    
    os.makedirs("demo_sites", exist_ok=True)
    
    # Choose theme color based on category
    theme_colors = {
        "dentist": {"primary": "sky-500", "accent": "sky-600", "icon": "🦷"},
        "dental": {"primary": "sky-500", "accent": "sky-600", "icon": "🦷"},
        "gym": {"primary": "red-500", "accent": "red-600", "icon": "💪"},
        "fitness": {"primary": "red-500", "accent": "red-600", "icon": "🏋️"},
        "salon": {"primary": "pink-500", "accent": "pink-600", "icon": "💇"},
        "spa": {"primary": "purple-500", "accent": "purple-600", "icon": "🧘"},
        "clinic": {"primary": "emerald-500", "accent": "emerald-600", "icon": "🏥"},
        "hospital": {"primary": "emerald-500", "accent": "emerald-600", "icon": "🏥"},
        "restaurant": {"primary": "orange-500", "accent": "orange-600", "icon": "🍽️"},
        "cafe": {"primary": "amber-500", "accent": "amber-600", "icon": "☕"},
        "school": {"primary": "blue-500", "accent": "blue-600", "icon": "🎓"},
    }
    
    category_lower = category.lower() if category else "business"
    theme = theme_colors.get(category_lower, {"primary": "indigo-500", "accent": "indigo-600", "icon": "🏢"})
    
    # Generate services based on category
    services = get_services_for_category(category)
    services_html = "\n".join([f'''
        <div class="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
            <div class="text-4xl mb-4">{service['icon']}</div>
            <h3 class="text-xl font-bold text-gray-800 mb-2">{service['title']}</h3>
            <p class="text-gray-600">{service['description']}</p>
        </div>
    ''' for service in services])
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{business_name} - Professional {category} Services</title>
    <meta name="description" content="{business_name} offers top-quality {category} services. Contact us today for a consultation.">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Inter', sans-serif; }}
        .gradient-bg {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
    </style>
</head>
<body class="bg-gray-50">
    <!-- Navigation -->
    <nav class="fixed w-full bg-white/95 backdrop-blur-sm shadow-sm z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16 items-center">
                <div class="flex items-center space-x-2">
                    <span class="text-2xl">{theme['icon']}</span>
                    <span class="text-xl font-bold text-gray-900">{business_name}</span>
                </div>
                <div class="hidden md:flex items-center space-x-8">
                    <a href="#services" class="text-gray-600 hover:text-{theme['primary']} transition">Services</a>
                    <a href="#about" class="text-gray-600 hover:text-{theme['primary']} transition">About</a>
                    <a href="#contact" class="text-gray-600 hover:text-{theme['primary']} transition">Contact</a>
                    <a href="#contact" class="bg-{theme['primary']} text-white px-6 py-2 rounded-full font-medium hover:bg-{theme['accent']} transition">
                        Book Now
                    </a>
                </div>
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="pt-24 pb-16 gradient-bg">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="grid md:grid-cols-2 gap-12 items-center">
                <div class="text-white">
                    <h1 class="text-4xl md:text-5xl lg:text-6xl font-extrabold mb-6 leading-tight">
                        Welcome to<br>{business_name}
                    </h1>
                    <p class="text-xl text-white/90 mb-8">
                        Your trusted partner for premium {category} services. 
                        We're committed to providing exceptional care and results that exceed your expectations.
                    </p>
                    <div class="flex flex-wrap gap-4">
                        <a href="#contact" class="bg-white text-{theme['accent']} px-8 py-4 rounded-full font-bold text-lg hover:bg-gray-100 transition shadow-lg">
                            Get Started Today
                        </a>
                        <a href="#services" class="border-2 border-white text-white px-8 py-4 rounded-full font-bold text-lg hover:bg-white/10 transition">
                            Our Services
                        </a>
                    </div>
                </div>
                <div class="hidden md:block">
                    <div class="bg-white/20 backdrop-blur-lg rounded-3xl p-8 text-center">
                        <div class="text-8xl mb-4">{theme['icon']}</div>
                        <p class="text-white text-xl font-medium">Excellence in {category}</p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Stats Section -->
    <section class="py-12 bg-white">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
                <div>
                    <div class="text-4xl font-bold text-{theme['primary']}">10+</div>
                    <div class="text-gray-600">Years Experience</div>
                </div>
                <div>
                    <div class="text-4xl font-bold text-{theme['primary']}">5000+</div>
                    <div class="text-gray-600">Happy Clients</div>
                </div>
                <div>
                    <div class="text-4xl font-bold text-{theme['primary']}">4.9</div>
                    <div class="text-gray-600">Average Rating</div>
                </div>
                <div>
                    <div class="text-4xl font-bold text-{theme['primary']}">100%</div>
                    <div class="text-gray-600">Satisfaction</div>
                </div>
            </div>
        </div>
    </section>

    <!-- Services Section -->
    <section id="services" class="py-20 bg-gray-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="text-center mb-16">
                <h2 class="text-3xl md:text-4xl font-bold text-gray-900 mb-4">Our Services</h2>
                <p class="text-xl text-gray-600 max-w-2xl mx-auto">
                    We offer a comprehensive range of {category} services to meet all your needs.
                </p>
            </div>
            <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                {services_html}
            </div>
        </div>
    </section>

    <!-- About Section -->
    <section id="about" class="py-20 bg-white">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="grid md:grid-cols-2 gap-12 items-center">
                <div class="bg-gradient-to-br from-{theme['primary']}/10 to-{theme['accent']}/10 rounded-3xl p-12">
                    <div class="text-9xl text-center">{theme['icon']}</div>
                </div>
                <div>
                    <h2 class="text-3xl md:text-4xl font-bold text-gray-900 mb-6">Why Choose Us?</h2>
                    <div class="space-y-4">
                        <div class="flex items-start space-x-4">
                            <div class="flex-shrink-0 w-6 h-6 bg-{theme['primary']} rounded-full flex items-center justify-center text-white text-sm">✓</div>
                            <div>
                                <h3 class="font-semibold text-gray-900">Experienced Professionals</h3>
                                <p class="text-gray-600">Our team brings years of expertise and dedication to every service.</p>
                            </div>
                        </div>
                        <div class="flex items-start space-x-4">
                            <div class="flex-shrink-0 w-6 h-6 bg-{theme['primary']} rounded-full flex items-center justify-center text-white text-sm">✓</div>
                            <div>
                                <h3 class="font-semibold text-gray-900">Modern Equipment</h3>
                                <p class="text-gray-600">We use the latest technology to ensure the best results.</p>
                            </div>
                        </div>
                        <div class="flex items-start space-x-4">
                            <div class="flex-shrink-0 w-6 h-6 bg-{theme['primary']} rounded-full flex items-center justify-center text-white text-sm">✓</div>
                            <div>
                                <h3 class="font-semibold text-gray-900">Customer Satisfaction</h3>
                                <p class="text-gray-600">Your satisfaction is our top priority. We go above and beyond.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Contact Section -->
    <section id="contact" class="py-20 bg-gray-900">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="text-center mb-12">
                <h2 class="text-3xl md:text-4xl font-bold text-white mb-4">Get In Touch</h2>
                <p class="text-xl text-gray-400">Ready to get started? Contact us today!</p>
            </div>
            <div class="max-w-2xl mx-auto">
                <form class="space-y-6">
                    <div class="grid md:grid-cols-2 gap-6">
                        <input type="text" placeholder="Your Name" class="w-full px-6 py-4 rounded-xl bg-gray-800 text-white placeholder-gray-400 border border-gray-700 focus:outline-none focus:border-{theme['primary']}">
                        <input type="email" placeholder="Your Email" class="w-full px-6 py-4 rounded-xl bg-gray-800 text-white placeholder-gray-400 border border-gray-700 focus:outline-none focus:border-{theme['primary']}">
                    </div>
                    <input type="tel" placeholder="Phone Number" class="w-full px-6 py-4 rounded-xl bg-gray-800 text-white placeholder-gray-400 border border-gray-700 focus:outline-none focus:border-{theme['primary']}">
                    <textarea rows="4" placeholder="Your Message" class="w-full px-6 py-4 rounded-xl bg-gray-800 text-white placeholder-gray-400 border border-gray-700 focus:outline-none focus:border-{theme['primary']}"></textarea>
                    <button type="submit" class="w-full bg-{theme['primary']} text-white py-4 rounded-xl font-bold text-lg hover:bg-{theme['accent']} transition">
                        Send Message
                    </button>
                </form>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="bg-gray-950 py-8">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <p class="text-gray-500">
                © {datetime.now().year} {business_name}. All rights reserved.
            </p>
            <p class="text-gray-600 text-sm mt-2">
                This is a demo website created to showcase design possibilities.
            </p>
        </div>
    </footer>
</body>
</html>'''
    
    with open(filepath, "w", encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"Generated demo site: {filename}")
    return f"/demo-sites/{filename}"


def get_services_for_category(category: str) -> list:
    """Get relevant services based on business category"""
    category_lower = category.lower() if category else "business"
    
    services_map = {
        "dentist": [
            {"icon": "🦷", "title": "General Dentistry", "description": "Comprehensive dental care including checkups, cleanings, and preventive treatments."},
            {"icon": "✨", "title": "Teeth Whitening", "description": "Professional whitening treatments for a brighter, more confident smile."},
            {"icon": "🔧", "title": "Restorative Care", "description": "Fillings, crowns, and repairs to restore your teeth to optimal health."},
        ],
        "dental": [
            {"icon": "🦷", "title": "General Dentistry", "description": "Regular checkups and preventive dental care."},
            {"icon": "✨", "title": "Cosmetic Dentistry", "description": "Enhance your smile with our cosmetic procedures."},
            {"icon": "👶", "title": "Pediatric Care", "description": "Gentle dental care for children of all ages."},
        ],
        "gym": [
            {"icon": "💪", "title": "Personal Training", "description": "One-on-one sessions with certified fitness experts."},
            {"icon": "🏃", "title": "Group Classes", "description": "High-energy group workouts for all fitness levels."},
            {"icon": "🎯", "title": "Weight Training", "description": "Build strength with our state-of-the-art equipment."},
        ],
        "salon": [
            {"icon": "💇", "title": "Hair Styling", "description": "Expert cuts, colors, and styling for all hair types."},
            {"icon": "💅", "title": "Nail Services", "description": "Manicures, pedicures, and nail art."},
            {"icon": "💆", "title": "Spa Treatments", "description": "Relaxing facials and body treatments."},
        ],
        "clinic": [
            {"icon": "🩺", "title": "General Medicine", "description": "Comprehensive healthcare for the whole family."},
            {"icon": "💉", "title": "Vaccinations", "description": "Stay protected with our immunization services."},
            {"icon": "🔬", "title": "Lab Services", "description": "On-site diagnostics and testing."},
        ],
    }
    
    # Return category-specific services or default
    return services_map.get(category_lower, [
        {"icon": "⭐", "title": "Premium Service", "description": "Top-quality service delivered by experienced professionals."},
        {"icon": "🎯", "title": "Custom Solutions", "description": "Tailored solutions to meet your specific needs."},
        {"icon": "🤝", "title": "Customer Support", "description": "Dedicated support to ensure your satisfaction."},
    ])
