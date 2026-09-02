"""E-ticaret taksonomisi: 25 ust kategori, her birinin altinda 8-10 nis.

Her nis icin ornek urun basliklari var; nis vektoru bu orneklerin embedding
ortalamasi olarak hesaplanir (bkz. vectors.py). Ornekler gercekci Shopify
urun basliklarini taklit eder - model bu sayede baslik dilini ogrenir.
"""
from __future__ import annotations

TAXONOMY: dict[str, dict[str, list[str]]] = {
    "Apparel": {
        "T-Shirts & Tops": ["Oversized Cotton Crewneck Tee", "Graphic Print T-Shirt Unisex", "Ribbed Crop Tank Top", "Vintage Washed Boxy Tee", "Long Sleeve Henley Shirt", "Muscle Fit V-Neck T-Shirt", "Funny Slogan Graphic Tee", "Quote Print Unisex T-Shirt", "Christmas Novelty T-Shirt"],
        "Hoodies & Sweatshirts": ["Heavyweight Fleece Pullover Hoodie", "Embroidered Logo Crewneck Sweatshirt", "Zip-Up Hoodie with Kangaroo Pocket", "Oversized Drop Shoulder Sweatshirt", "Sherpa Lined Hooded Jacket", "Cropped Raw Hem Hoodie", "Slogan Print Sweatshirt Unisex", "Holiday Novelty Hoodie"],
        "Dresses": ["Floral Midi Wrap Dress", "Satin Slip Cocktail Dress", "Bodycon Ruched Mini Dress", "Linen Sleeveless Maxi Dress", "Puff Sleeve Smocked Sundress", "Knit Sweater Dress"],
        "Bottoms & Jeans": ["High Waisted Wide Leg Jeans", "Stretch Skinny Denim Pants", "Pleated Tailored Trousers", "Cargo Jogger Pants", "Distressed Mom Jeans", "Corduroy Straight Leg Pants"],
        "Outerwear & Jackets": ["Quilted Puffer Jacket", "Faux Leather Biker Jacket", "Wool Blend Trench Coat", "Windbreaker Shell Jacket", "Denim Trucker Jacket Sherpa", "Longline Padded Parka"],
        "Activewear & Leggings": ["High Waist Seamless Leggings", "Buttery Soft Yoga Pants", "Compression Sports Bra", "Quick Dry Running Shorts", "Ribbed Workout Set Two Piece", "Athletic Performance Joggers"],
        "Swimwear": ["High Cut One Piece Swimsuit", "Ribbed Triangle Bikini Set", "Tummy Control Tankini", "Board Shorts Quick Dry", "Ruffle Bandeau Swim Top", "Mesh Beach Cover Up"],
        "Lingerie & Sleepwear": ["Lace Bralette Wireless", "Seamless Shapewear Bodysuit", "Satin Pajama Set Long Sleeve", "Cotton Boyshort Briefs Pack", "Silk Robe Kimono", "Thermal Waffle Knit Loungewear"],
        "Hats & Accessories": ["Straw Sun Hat Wide Brim", "Embroidered Dad Cap Cotton", "Knit Beanie Winter Unisex", "Bucket Hat Reversible", "Silk Scarf Printed Square", "Leather Belt Reversible Buckle", "Touchscreen Winter Gloves", "Baseball Cap Adjustable Strap"],
        "Suits & Formalwear": ["Slim Fit Two Piece Suit", "Tuxedo Dinner Jacket Shawl Lapel", "Formal Dress Shirt Non Iron", "Waistcoat Vest Tailored", "Mother of the Bride Gown", "Prom Ball Gown Sequin"],
    },
    "Footwear": {
        "Sneakers": ["Chunky Platform Sneakers", "Retro Running Shoes Mesh", "Canvas Low Top Trainers", "Knit Slip On Sneakers", "High Top Basketball Shoes", "Lightweight Walking Sneakers"],
        "Boots": ["Chelsea Ankle Boots Leather", "Combat Lace Up Boots", "Knee High Riding Boots", "Waterproof Hiking Boots", "Shearling Lined Snow Boots", "Western Cowboy Boots"],
        "Sandals & Flip Flops": ["Strappy Flat Sandals", "Platform Espadrille Wedges", "Arch Support Slide Sandals", "Leather Thong Flip Flops", "Gladiator Lace Up Sandals", "EVA Cloud Slides"],
        "Heels & Dress Shoes": ["Pointed Toe Stiletto Pumps", "Block Heel Ankle Strap Sandals", "Oxford Leather Dress Shoes", "Loafers Penny Slip On", "Kitten Heel Slingback", "Patent Leather Derby Shoes"],
        "Flats & Loafers": ["Ballet Flats Pointed Toe", "Suede Driving Moccasins", "Mary Jane Flat Shoes", "Woven Leather Mules", "Foldable Travel Flats", "Chunky Loafers Lug Sole"],
        "Slippers & House Shoes": ["Memory Foam Slippers Fleece", "Fuzzy Slide Slippers", "Moccasin House Shoes Suede", "Open Toe Spa Slippers", "Indoor Outdoor Clog Slippers", "Heated Microwavable Slippers"],
        "Kids Shoes": ["Toddler Velcro Sneakers", "Kids Rain Boots Rubber", "School Uniform Shoes Black", "Light Up LED Sneakers", "Baby Soft Sole Pre Walker", "Youth Soccer Cleats"],
        "Shoe Care & Insoles": ["Orthotic Arch Support Insoles", "Gel Heel Cushion Pads", "Suede Cleaning Brush Kit", "Waterproofing Spray for Leather", "Shoe Stretcher Wooden", "Odor Eliminating Shoe Deodorizer"],
    },
    "Jewelry & Watches": {
        "Necklaces & Pendants": ["Dainty Gold Layered Necklace", "Initial Letter Pendant Necklace", "Freshwater Pearl Choker", "Sterling Silver Cuban Chain", "Birthstone Charm Necklace", "Personalized Bar Nameplate Necklace"],
        "Rings": ["Stackable Thin Band Rings Set", "Moissanite Engagement Ring", "Chunky Signet Ring Gold", "Adjustable Open Cuff Ring", "Tungsten Wedding Band Men", "Vintage Opal Statement Ring"],
        "Earrings": ["Chunky Gold Hoop Earrings", "Cubic Zirconia Stud Earrings", "Threader Drop Earrings", "Huggie Hoops Hypoallergenic", "Pearl Cluster Statement Earrings", "Clip On Earrings Non Pierced"],
        "Bracelets & Anklets": ["Beaded Stretch Bracelet Set", "Tennis Bracelet Cubic Zirconia", "Leather Wrap Cuff Bracelet", "Cuban Link Chain Bracelet", "Ankle Chain Layered Anklet", "Engraved Bangle Personalized"],
        "Watches": ["Minimalist Mesh Strap Watch", "Automatic Skeleton Dive Watch", "Digital Sports Chronograph Watch", "Rose Gold Ladies Wristwatch", "Leather Band Dress Watch", "Vintage Field Watch Nylon Strap"],
        "Body & Piercing Jewelry": ["Surgical Steel Nose Stud", "Belly Button Ring Dangle", "Cartilage Helix Hoop Set", "Septum Clicker Titanium", "Industrial Barbell Piercing", "Nipple Ring Hypoallergenic"],
        "Mens Jewelry": ["Stainless Steel Cross Pendant", "Beaded Lava Stone Bracelet Men", "Signet Ring Stainless Steel", "Dog Tag Chain Necklace", "Cufflinks Set Formal", "Leather Braided Wristband"],
        "Jewelry Storage & Care": ["Velvet Jewelry Box Organizer", "Travel Jewelry Roll Pouch", "Ring Display Stand Holder", "Silver Polishing Cloth Kit", "Ultrasonic Jewelry Cleaner", "Wall Mounted Necklace Rack"],
    },
    "Bags & Luggage": {
        "Handbags & Totes": ["Quilted Crossbody Shoulder Bag", "Canvas Tote Bag Large", "Structured Leather Satchel", "Woven Straw Beach Tote", "Hobo Slouchy Shoulder Bag", "Mini Baguette Bag Trendy"],
        "Backpacks": ["Anti Theft Travel Backpack", "Laptop Backpack 15 inch USB", "Rolltop Waterproof Daypack", "Mini Leather Fashion Backpack", "Hiking Backpack 40L Frame", "Kids School Backpack Cartoon"],
        "Wallets & Cardholders": ["RFID Blocking Slim Wallet", "Bifold Leather Wallet Men", "Zip Around Clutch Wallet", "Minimalist Metal Card Holder", "Travel Passport Wallet Organizer", "Chain Wallet Long Purse"],
        "Luggage & Suitcases": ["Hardshell Spinner Carry On", "Expandable Checked Luggage Set", "Duffel Bag with Shoe Compartment", "Garment Bag for Suits", "Underseat Rolling Tote", "Aluminum Frame Trolley Case"],
        "Travel Accessories": ["Packing Cubes Set of 6", "Memory Foam Travel Neck Pillow", "TSA Approved Toiletry Bag", "Luggage Scale Digital", "Compression Vacuum Travel Bags", "Universal Travel Power Adapter"],
        "Belt Bags & Fanny Packs": ["Nylon Belt Bag Adjustable", "Leather Fanny Pack Crossbody", "Running Waist Pouch Phone", "Sling Chest Bag Unisex", "Hiking Hip Pack with Bottle Holder", "Quilted Bum Bag Designer Style"],
        "Laptop & Tech Bags": ["Padded Laptop Sleeve 13 inch", "Camera Shoulder Bag Insert", "Tech Organizer Cable Pouch", "Messenger Briefcase Leather", "Tablet Carrying Case Handle", "Rolling Laptop Case Business"],
        "Kids & School Bags": ["Toddler Mini Backpack Harness", "Insulated Lunch Bag Kids", "Rolling School Bag Wheels", "Character Print Sling Bag", "Drawstring Gym Sack", "Pencil Case Large Capacity"],
    },
    "Beauty & Cosmetics": {
        "Skincare": ["Vitamin C Brightening Serum", "Hyaluronic Acid Hydrating Moisturizer", "Retinol Night Cream Anti Aging", "Gentle Foaming Face Cleanser", "Niacinamide Pore Minimizing Toner", "Clay Detox Face Mask", "Sunscreen SPF 50 Face Spray", "Mineral Sunscreen Stick Kids", "Bar Soap Natural Cold Process"],
        "Makeup - Face": ["Full Coverage Liquid Foundation", "Cream Blush Stick Dewy", "Translucent Setting Powder", "Color Correcting Concealer", "Matte Contour Palette", "Illuminating Liquid Highlighter"],
        "Makeup - Eyes": ["Waterproof Volumizing Mascara", "Nude Eyeshadow Palette 18 Shades", "Precision Liquid Eyeliner Pen", "Brow Pencil Microblading Effect", "Magnetic Lashes with Eyeliner", "Glitter Eyeshadow Cream Pot"],
        "Makeup - Lips": ["Matte Liquid Lipstick Long Wear", "Tinted Lip Balm SPF", "Plumping Lip Gloss Shine", "Lip Liner Pencil Set", "Lip Sleeping Mask Overnight", "Velvet Lip Stain Transfer Proof"],
        "Haircare": ["Sulfate Free Repair Shampoo", "Deep Conditioning Hair Mask", "Argan Oil Hair Serum Frizz", "Dry Shampoo Volumizing Spray", "Curl Defining Cream", "Scalp Scrub Exfoliating Treatment"],
        "Nails": ["Gel Nail Polish Kit UV Lamp", "Press On Nails Almond Shape", "Cuticle Oil Pen Nourishing", "Nail Art Stickers Set", "Quick Dry Top Coat", "Electric Nail Drill Manicure Kit"],
        "Fragrance": ["Eau de Parfum Floral Woody", "Rollerball Perfume Oil", "Body Mist Fine Fragrance", "Solid Perfume Balm Travel", "Cologne Spray Fresh Citrus", "Discovery Set Perfume Samples"],
        "Beauty Tools": ["Jade Roller Gua Sha Set", "Silicone Facial Cleansing Brush", "Makeup Brush Set 15 Piece", "LED Light Therapy Face Mask", "Blackhead Vacuum Pore Extractor", "Heatless Curling Rod Headband"],
        "Mens Grooming": ["Beard Growth Oil and Balm Kit", "Safety Razor Double Edge", "Matte Hair Clay Strong Hold", "Electric Body Groomer Trimmer", "Aftershave Balm Soothing", "Charcoal Face Wash for Men"],
    },
    "Health & Wellness": {
        "Vitamins & Supplements": ["Vegan Collagen Peptides Powder", "Magnesium Glycinate Capsules", "Ashwagandha Stress Support", "Multivitamin Gummies Adults", "Omega 3 Fish Oil Softgels", "Probiotic 50 Billion CFU"],
        "Fitness Recovery": ["Foam Roller Deep Tissue", "Massage Gun Percussion Handheld", "Compression Calf Sleeves", "Hot Cold Gel Ice Pack Wrap", "Muscle Recovery Balm Menthol", "Acupressure Mat and Pillow Set"],
        "Sleep & Relaxation": ["Weighted Blanket 15 lbs", "Silk Sleep Mask Contoured", "White Noise Sound Machine", "Melatonin Free Sleep Gummies", "Cooling Pillow Gel Memory Foam", "Lavender Pillow Mist Spray"],
        "Personal Care Devices": ["Digital Body Weight Scale", "Blood Pressure Monitor Upper Arm", "Infrared Forehead Thermometer", "Pulse Oximeter Fingertip", "TENS Unit Muscle Stimulator", "Posture Corrector Back Brace"],
        "Oral Care": ["Sonic Electric Toothbrush", "Water Flosser Cordless", "Charcoal Teeth Whitening Strips", "Tongue Scraper Copper", "Fluoride Free Toothpaste Tablets", "Night Guard Teeth Grinding"],
        "Aromatherapy & Essential Oils": ["Ultrasonic Essential Oil Diffuser", "Lavender Essential Oil 100% Pure", "Reed Diffuser Set Home Fragrance", "Aromatherapy Shower Steamers", "Roll On Essential Oil Blend", "Car Vent Diffuser Clip"],
        "Mobility & Daily Aids": ["Adjustable Walking Cane Folding", "Compression Socks Graduated", "Pill Organizer Weekly 7 Day", "Reacher Grabber Tool", "Knee Brace Patella Support", "Shower Chair Non Slip"],
        "Sexual Wellness": ["Water Based Personal Lubricant", "Couples Massage Oil Set", "Silicone Menstrual Cup", "Kegel Exercise Weights Set", "Intimate Wash pH Balanced", "Discreet Storage Case"],
    },
    "Home & Kitchen": {
        "Cookware & Bakeware": ["Nonstick Ceramic Frying Pan", "Cast Iron Dutch Oven Enameled", "Stainless Steel Saucepan Set", "Silicone Baking Mat Set", "Carbon Steel Wok Flat Bottom", "Springform Cake Pan Nonstick"],
        "Kitchen Gadgets": ["Electric Milk Frother Handheld", "Vegetable Spiralizer Slicer", "Digital Kitchen Scale Grams", "Garlic Press Stainless Steel", "Silicone Collapsible Colander", "Herb Scissors Five Blade"],
        "Small Appliances": ["Air Fryer 5.5L Digital", "Espresso Machine with Steam Wand", "High Speed Blender 1200W", "Electric Kettle Gooseneck", "Stand Mixer 5 Quart", "Rice Cooker Multi Function"],
        "Tableware & Drinkware": ["Stoneware Dinner Plate Set", "Insulated Stainless Steel Tumbler", "Crystal Wine Glass Set of 4", "Bamboo Serving Tray", "Ceramic Mug Handmade Speckled", "Glass Water Carafe with Lid", "20oz Insulated Tumbler with Straw", "Ceramic Quote Mug 11oz", "Skinny Tumbler Sublimation Blank"],
        "Food Storage": ["Airtight Pantry Storage Containers", "Vacuum Sealer Machine Bags", "Reusable Silicone Food Bags", "Glass Meal Prep Containers", "Bread Box Stainless Steel", "Stackable Fridge Organizer Bins"],
        "Cleaning & Laundry": ["Microfiber Cleaning Cloth Pack", "Spin Mop and Bucket System", "Steam Cleaner Handheld", "Wool Dryer Balls Set", "Laundry Sorter Hamper 3 Section", "Grout Cleaning Brush Set"],
        "Bedding & Linens": ["Bamboo Cooling Sheet Set Queen", "Down Alternative Comforter", "Waffle Weave Duvet Cover", "Memory Foam Pillow Cervical", "Waterproof Mattress Protector", "Linen Pillowcase Set of 2"],
        "Bath": ["Turkish Cotton Bath Towel Set", "Rainfall Shower Head High Pressure", "Bamboo Bath Caddy Tray", "Memory Foam Bath Mat Non Slip", "Shower Curtain Waffle Fabric", "Bathroom Organizer Corner Shelf"],
        "Home Organization": ["Under Bed Storage Bags Zippered", "Closet Hanging Shelf Organizer", "Drawer Divider Adjustable", "Shoe Rack 5 Tier Stackable", "Cable Management Box", "Label Maker Machine Portable"],
    },
    "Furniture & Decor": {
        "Living Room Furniture": ["Mid Century Modern Accent Chair", "Convertible Sleeper Sofa Bed", "Marble Top Coffee Table", "Boucle Swivel Armchair", "Nesting Side Table Set", "Modular Sectional Sofa Chaise"],
        "Bedroom Furniture": ["Upholstered Platform Bed Frame", "6 Drawer Dresser Wood", "Floating Nightstand Wall Mount", "Cheval Full Length Mirror", "Storage Ottoman Bench End of Bed", "Rattan Headboard King"],
        "Office Furniture": ["Electric Standing Desk Adjustable", "Ergonomic Mesh Office Chair", "L Shaped Corner Computer Desk", "Rolling File Cabinet 3 Drawer", "Bookshelf 5 Tier Industrial", "Monitor Riser Stand with Storage"],
        "Wall Art & Prints": ["Abstract Canvas Wall Art Set", "Botanical Line Drawing Print", "Vintage Movie Poster Framed", "Macrame Wall Hanging Boho", "Metal Wall Sculpture Modern", "Personalized Family Name Sign", "Alcohol Ink Art Print Wildlife", "Digital Download Wall Art Printable"],
        "Rugs & Textiles": ["Washable Area Rug 5x7", "Jute Braided Round Rug", "Chunky Knit Throw Blanket", "Velvet Cushion Cover Set", "Linen Curtain Panels Blackout", "Runner Rug Hallway Nonslip"],
        "Mirrors & Frames": ["Arched Full Length Floor Mirror", "Gallery Wall Picture Frame Set", "LED Backlit Vanity Mirror", "Sunburst Wall Mirror Gold", "Acrylic Photo Frame Magnetic", "Antique Ornate Wall Mirror"],
        "Decorative Accents": ["Ceramic Vase Set Minimalist", "Scented Soy Candle Amber Jar", "Decorative Coffee Table Books", "Brass Bookend Pair", "Faux Olive Tree Potted", "Wooden Beaded Garland Boho"],
        "Storage Furniture": ["Sideboard Buffet Cabinet", "Storage Bench with Cushion", "Rattan Basket Set Woven", "Entryway Console Table Narrow", "Shoe Cabinet Slim Tipping", "Cube Storage Organizer 9 Cube"],
    },
    "Lighting": {
        "Ceiling & Pendant Lights": ["Rattan Pendant Light Shade", "Sputnik Chandelier Brass", "Flush Mount LED Ceiling Light", "Industrial Cage Pendant Lamp", "Linear Dining Room Chandelier", "Paper Lantern Ceiling Shade"],
        "Table & Floor Lamps": ["Arc Floor Lamp Marble Base", "Ceramic Table Lamp Linen Shade", "Tripod Wooden Floor Lamp", "Mushroom Bedside Lamp Glass", "Adjustable Reading Floor Lamp", "Touch Control Nightstand Lamp"],
        "String & Fairy Lights": ["Outdoor Cafe String Lights", "Copper Wire Fairy Lights Battery", "Curtain Icicle Lights Remote", "Solar Powered Globe Lights", "Photo Clip String Lights", "Festoon Bulb Lights Waterproof"],
        "Smart & LED Lighting": ["Smart RGB LED Strip Lights", "WiFi Smart Bulb Color Changing", "Motion Sensor LED Cabinet Light", "Hexagon Wall Light Panels", "Sunset Projection Lamp", "Dimmable Smart Downlight Set"],
        "Outdoor Lighting": ["Solar Pathway Lights Stake", "LED Flood Light Security Motion", "Hanging Solar Lantern Garden", "Deck Step Lights Low Voltage", "Wall Sconce Outdoor Waterproof", "Solar Fence Post Cap Lights"],
        "Desk & Task Lighting": ["LED Desk Lamp with USB Port", "Clip On Book Light Rechargeable", "Ring Light with Tripod Stand", "Under Cabinet Puck Lights", "Magnifying Lamp for Crafts", "Architect Swing Arm Desk Lamp"],
        "Novelty & Mood Lighting": ["Neon Sign LED Custom", "Lava Lamp Retro", "Galaxy Star Projector Night Light", "Himalayan Salt Lamp", "Moon Lamp 3D Printed", "Levitating Floating Light Bulb"],
        "Candles & Holders": ["Taper Candle Holder Brass Set", "Beeswax Pillar Candles", "Hurricane Glass Candle Lantern", "Flameless LED Candles Remote", "Tealight Holder Ceramic Set", "Candle Snuffer and Wick Trimmer"],
    },
    "Garden & Outdoor": {
        "Planters & Pots": ["Ceramic Planter with Drainage", "Self Watering Plant Pot", "Hanging Macrame Plant Hanger", "Raised Garden Bed Cedar", "Terracotta Pot Set of 3", "Grow Bags Fabric 10 Gallon"],
        "Garden Tools": ["Ergonomic Garden Trowel Set", "Bypass Pruning Shears", "Expandable Garden Hose 50ft", "Kneeling Pad and Seat", "Weeding Fork Long Handle", "Watering Can Copper Finish"],
        "Seeds & Plants": ["Heirloom Tomato Seed Variety Pack", "Wildflower Seed Mix Pollinator", "Indoor Herb Garden Starter Kit", "Succulent Cuttings Assorted", "Microgreens Growing Kit", "Air Plant Tillandsia Set"],
        "Outdoor Furniture": ["Acacia Wood Patio Dining Set", "Folding Adirondack Chair", "Hanging Egg Chair with Stand", "Outdoor Sectional with Cushions", "Bistro Table Set Balcony", "Zero Gravity Recliner Chair"],
        "Grills & Outdoor Cooking": ["Portable Charcoal Grill Tabletop", "Pellet Smoker Grill", "Cast Iron Griddle Camping", "Pizza Oven Outdoor Wood Fired", "Grill Tool Set Stainless", "Fire Pit Table Propane"],
        "Lawn Care": ["Cordless Grass Trimmer Battery", "Hose Reel Cart Wheeled", "Fertilizer Spreader Broadcast", "Leaf Blower Cordless", "Lawn Aerator Spike Shoes", "Sprinkler Oscillating Adjustable"],
        "Pest & Weather Protection": ["Solar Mosquito Zapper Lantern", "Garden Netting Plant Protection", "Ultrasonic Rodent Repeller", "Frost Blanket Plant Cover", "Patio Umbrella with Base", "Greenhouse Mini Walk In"],
        "Outdoor Decor": ["Wind Chime Bamboo Deep Tone", "Garden Gnome Statue Resin", "Bird Feeder Squirrel Proof", "Solar Water Fountain Pump", "Stepping Stones Decorative", "Outdoor Doormat Coir"],
    },
    "Pet Supplies": {
        "Dog Accessories": ["No Pull Dog Harness Adjustable", "Retractable Dog Leash 16ft", "Personalized Dog Collar Engraved", "Waterproof Dog Raincoat", "Dog Seat Cover Car Hammock", "Slip Lead Rope Training"],
        "Cat Supplies": ["Cat Tree Tower Multi Level", "Self Cleaning Litter Box", "Interactive Cat Wand Toy", "Cat Window Perch Suction", "Ceramic Whisker Friendly Bowl", "Catnip Scratching Post Sisal"],
        "Pet Beds & Furniture": ["Orthopedic Memory Foam Dog Bed", "Calming Donut Cuddler Bed", "Elevated Cooling Pet Cot", "Pet Sofa Cover Protector", "Cave Bed for Cats Felt", "Heated Pet Bed Pad"],
        "Pet Toys": ["Indestructible Chew Toy Rubber", "Treat Dispensing Puzzle Ball", "Squeaky Plush Dog Toy Set", "Automatic Ball Launcher", "Snuffle Mat Enrichment", "Laser Pointer Cat Toy Automatic"],
        "Pet Grooming": ["Deshedding Brush Undercoat Rake", "Pet Nail Grinder Quiet", "Dog Clippers Cordless Kit", "Waterless Pet Shampoo Foam", "Grooming Glove Deshedding", "Pet Hair Dryer Blower"],
        "Feeding & Water": ["Automatic Pet Feeder Timed", "Stainless Steel Slow Feeder Bowl", "Pet Water Fountain Filtered", "Elevated Dog Bowl Stand", "Collapsible Travel Water Bottle", "Airtight Pet Food Storage Bin"],
        "Pet Health": ["Dog Dental Chews Breath", "Flea and Tick Collar", "Joint Supplement Chews Glucosamine", "Pet Calming Diffuser Spray", "Paw Balm Protective Wax", "Ear Cleaning Solution Pets", "Dog Ear Muffs Noise Protection", "Pet Anxiety Calming Wrap"],
        "Small Pets & Aquarium": ["Hamster Cage with Tunnels", "Aquarium LED Light Bar", "Reptile Heat Lamp Fixture", "Bird Cage Play Top Stand", "Rabbit Hay Feeder Rack", "Fish Tank Filter Quiet"],
    },
    "Baby & Kids": {
        "Baby Clothing": ["Organic Cotton Baby Onesie Set", "Footed Sleeper Zip Pajamas", "Muslin Swaddle Blanket Pack", "Knitted Baby Romper", "Bandana Drool Bib Set", "Newborn Coming Home Outfit"],
        "Feeding & Nursing": ["Anti Colic Baby Bottle Set", "Silicone Bib with Food Catcher", "Electric Breast Pump Double", "Bottle Warmer and Sterilizer", "Toddler Snack Cup Spill Proof", "Nursing Pillow Cover", "Wooden High Chair Adjustable", "Booster Seat for Dining Table", "Convertible High Chair 3 in 1"],
        "Nursery & Sleep": ["Convertible Crib 4 in 1", "Baby Monitor Video WiFi", "Blackout Nursery Curtains", "Sleep Sack Wearable Blanket", "Changing Pad Waterproof Cover", "Nursery Storage Baskets Set", "Crib Sheet Set Fitted Cotton", "Crib Bedding Set 3 Piece", "Travel Cot Folding Playard", "Changing Mat Padded Waterproof", "Changing Table with Wheels"],
        "Strollers & Car Seats": ["Lightweight Travel Stroller Folding", "Convertible Car Seat Rear Facing", "Stroller Organizer Caddy", "Baby Carrier Ergonomic Hip Seat", "Car Seat Sun Shade Cover", "Double Jogging Stroller"],
        "Baby Safety": ["Cabinet Safety Locks Magnetic", "Retractable Baby Gate Doorway", "Corner Edge Protector Guards", "Outlet Plug Covers Pack", "Anti Tip Furniture Straps", "Toilet Lock Child Proof"],
        "Bath & Diapering": ["Baby Bath Tub Foldable", "Diaper Caddy Organizer Portable", "Hooded Baby Towel Bamboo", "Wipe Warmer Dispenser", "Reusable Cloth Diapers Set", "Baby Shampoo Tear Free", "Muslin Washcloth Set Bamboo", "Non Slip Bath Mat for Kids", "Baby Bath Kneeler Pad"],
        "Kids Clothing": ["Toddler Graphic Tee 2 Pack", "Kids Rain Jacket Hooded", "Girls Tulle Party Dress", "Boys Cargo Shorts Elastic", "Kids Thermal Base Layer Set", "Matching Sibling Pajama Set"],
        "Kids Room & Play": ["Play Tent Teepee Indoor", "Toy Storage Organizer Bins", "Kids Table and Chair Set", "Growth Chart Wooden Ruler", "Foam Play Mat Interlocking", "Kids Reading Nook Book Rack", "Baby Walker Activity Push Toy", "Foam Puzzle Play Mat Interlocking", "Baby Activity Center Bouncer"],
    },
    "Toys & Games": {
        "Educational Toys": ["Montessori Wooden Busy Board", "STEM Building Blocks Magnetic", "Alphabet Learning Flash Cards", "Kids Microscope Science Kit", "Coding Robot Toy for Kids", "Solar System Planetarium Model"],
        "Building & Construction": ["Magnetic Tiles 100 Piece Set", "Wooden Train Track Set", "Marble Run Maze Builder", "Interlocking Brick Building Kit", "Gear Construction Set Spinning", "Foam Blocks Soft Building Set"],
        "Dolls & Figures": ["Fashion Doll with Accessories", "Action Figure Articulated", "Baby Doll with Feeding Set", "Collectible Vinyl Art Figure", "Dollhouse Furniture Miniature", "Plush Stuffed Animal Weighted"],
        "Board Games & Puzzles": ["Strategy Board Game 2 to 4 Players", "1000 Piece Jigsaw Puzzle Landscape", "Family Card Game Party", "Wooden Brain Teaser Puzzle Set", "Cooperative Escape Room Game", "Chess Set Magnetic Travel"],
        "Outdoor Play": ["Inflatable Kiddie Pool", "Water Balloon Quick Fill Set", "Kids Scooter 3 Wheel LED", "Backyard Bounce House", "Sandbox Toys Beach Set", "Slackline Kit for Kids"],
        "RC & Drones": ["Remote Control Stunt Car", "Mini Drone with Camera Beginner", "RC Monster Truck Off Road", "RC Boat Waterproof Fast", "Robot Dog Remote Control", "Racing Drone FPV Kit"],
        "Arts & Craft Toys": ["Kids Painting Easel Double Sided", "Air Dry Clay Modeling Kit", "Jewelry Making Kit for Girls", "Scratch Art Paper Set", "Kinetic Sand Play Set", "DIY Slime Making Kit"],
        "Sensory & Fidget": ["Pop It Fidget Toy Set", "Weighted Sensory Lap Pad", "Liquid Motion Bubbler Timer", "Chewy Sensory Necklace", "Infinity Cube Fidget Metal", "Kinetic Desk Toy Spinner"],
    },
    "Electronics": {
        "Headphones & Audio": ["Wireless Noise Cancelling Headphones", "True Wireless Earbuds ANC", "Bluetooth Portable Speaker Waterproof", "Open Ear Bone Conduction Headphones", "Studio Monitor Headphones Wired", "Soundbar with Subwoofer"],
        "Smart Home Devices": ["Smart Plug WiFi 4 Pack", "Video Doorbell Camera Wireless", "Smart Thermostat Programmable", "Robot Vacuum with Mapping", "Smart Door Lock Keypad", "Indoor Security Camera Pan Tilt"],
        "Wearable Tech": ["Fitness Tracker Heart Rate", "Smartwatch AMOLED GPS", "Smart Ring Sleep Tracker", "Bluetooth Sleep Headband", "Kids GPS Tracker Watch", "Smart Glasses Audio"],
        "Computers & Peripherals": ["Mechanical Gaming Keyboard RGB", "Wireless Ergonomic Vertical Mouse", "USB C Docking Station Hub", "Portable Monitor 15.6 inch", "External SSD 1TB Type C", "Webcam 1080p with Ring Light"],
        "Cameras & Drones": ["Action Camera 4K Waterproof", "Vlogging Camera with Flip Screen", "Instant Print Camera", "Gimbal Stabilizer Smartphone", "Trail Camera Night Vision", "Camera Lens Filter Kit"],
        "Gaming Accessories": ["Wireless Controller with Paddles", "Gaming Headset Surround Sound", "Console Cooling Stand", "Arcade Fight Stick", "Gaming Mouse Pad XXL RGB", "Handheld Retro Game Console"],
        "TV & Projectors": ["Mini Projector 1080p Portable", "Streaming Media Stick 4K", "TV Wall Mount Full Motion", "HDMI Splitter 4K 60Hz", "Universal Remote Control Smart", "Antenna Indoor HDTV Amplified"],
        "Power & Charging": ["Portable Power Bank 20000mAh", "GaN Fast Charger 65W", "Wireless Charging Stand 3 in 1", "Solar Panel Charger Foldable", "Portable Power Station 300W", "Surge Protector Power Strip USB"],
    },
    "Phone & Computer Accessories": {
        "Phone Cases": ["Clear MagSafe Phone Case", "Rugged Shockproof Case with Stand", "Silicone Case with Camera Cover", "Wallet Case Card Holder Leather", "Biodegradable Phone Case", "Crossbody Phone Case with Strap"],
        "Screen Protectors": ["Tempered Glass Screen Protector 3 Pack", "Privacy Screen Protector Anti Spy", "Matte Anti Glare Film", "Camera Lens Protector Metal Ring", "Laptop Screen Privacy Filter", "Watch Screen Protector Case"],
        "Cables & Adapters": ["USB C to Lightning Braided Cable", "Multi Charging Cable 3 in 1", "HDMI Cable 4K High Speed", "USB C to Ethernet Adapter", "Magnetic Charging Cable Tips", "Right Angle Charging Cable Gaming"],
        "Phone Mounts & Stands": ["Car Phone Mount Magnetic Vent", "Adjustable Desk Phone Stand", "Bike Handlebar Phone Holder", "Gooseneck Bed Phone Holder", "Tripod Selfie Stick Bluetooth", "Ring Grip Holder Collapsible"],
        "Laptop Accessories": ["Laptop Stand Aluminum Adjustable", "Keyboard Cover Skin Silicone", "Laptop Cooling Pad Fan", "USB C Hub 7 in 1", "Lap Desk with Cushion", "Anti Theft Laptop Lock Cable"],
        "Tablet & E-Reader": ["Tablet Case with Pencil Holder", "Stylus Pen Palm Rejection", "Tablet Floor Stand Adjustable", "E-Reader Sleeve Felt", "Tablet Keyboard Case Detachable", "Paperlike Screen Film"],
        "Storage & Memory": ["MicroSD Card 256GB Class 10", "USB Flash Drive Dual Connector", "External Hard Drive 2TB Portable", "SD Card Reader USB C", "NVMe SSD Enclosure", "Memory Card Storage Case"],
        "Audio Accessories": ["Earbud Case Cover Silicone", "Headphone Stand Desk Hook", "Bluetooth Audio Transmitter Receiver", "Ear Tips Replacement Foam", "3.5mm Audio Splitter", "Microphone Pop Filter Shield"],
    },
    "Sports & Fitness": {
        "Home Gym Equipment": ["Adjustable Dumbbell Set", "Resistance Bands Set with Handles", "Foldable Weight Bench Incline", "Kettlebell Vinyl Coated", "Pull Up Bar Doorway", "Suspension Trainer Straps"],
        "Yoga & Pilates": ["Non Slip Yoga Mat 6mm", "Cork Yoga Block Set", "Pilates Ring Magic Circle", "Yoga Wheel Back Stretcher", "Meditation Cushion Buckwheat", "Yoga Strap with Loops"],
        "Cardio Equipment": ["Foldable Treadmill Under Desk", "Magnetic Exercise Bike Indoor", "Jump Rope Weighted Speed", "Mini Stepper with Bands", "Rowing Machine Magnetic", "Vertical Climber Exercise Machine"],
        "Team Sports": ["Indoor Outdoor Basketball Composite", "Soccer Ball Size 5 Match", "Volleyball Net Portable Set", "Baseball Glove Leather Youth", "Field Hockey Stick Composite", "Rugby Training Cones Set"],
        "Racquet Sports": ["Pickleball Paddle Set with Balls", "Tennis Racket Pre Strung", "Badminton Set Portable Net", "Table Tennis Paddle Set", "Squash Racquet Lightweight", "Racket Grip Overgrip Tape"],
        "Water Sports": ["Inflatable Paddle Board Kit", "Snorkel Mask Full Face", "Swim Goggles Anti Fog", "Kayak Paddle Adjustable", "Dry Bag Waterproof 20L", "Neoprene Wetsuit Shorty"],
        "Cycling": ["Bike Repair Tool Kit Portable", "Cycling Helmet with LED Light", "Bike Phone Mount Waterproof", "Padded Cycling Shorts", "Bike Floor Pump Gauge", "Bicycle Panniers Rear Rack Bag"],
        "Fitness Accessories": ["Gym Duffel Bag Wet Pocket", "Lifting Straps Wrist Wraps", "Insulated Shaker Bottle", "Ab Roller Wheel Knee Pad", "Workout Gloves Grip", "Sweat Waist Trainer Belt"],
    },
    "Outdoor & Adventure": {
        "Camping Gear": ["4 Person Instant Pop Up Tent", "Sleeping Bag 20 Degree Mummy", "Self Inflating Sleeping Pad", "Camping Cot Folding Portable", "Camp Chair Compact Lightweight", "Hammock with Tree Straps"],
        "Hiking & Backpacking": ["Trekking Poles Carbon Fiber", "Hydration Bladder 2L Pack", "Ultralight Backpacking Stove", "Compass and Whistle Kit", "Gaiters Waterproof Hiking", "Dry Sack Compression"],
        "Survival & Emergency": ["Emergency Survival Kit Bag", "Fire Starter Ferro Rod", "Water Filter Straw Portable", "Emergency Mylar Blanket Pack", "Multi Tool Pliers Stainless", "Hand Crank Emergency Radio"],
        "Fishing": ["Telescopic Fishing Rod and Reel Combo", "Tackle Box Organizer Trays", "Soft Plastic Lure Kit", "Fishing Line Braided 30lb", "Fillet Knife with Sheath", "Fish Finder Portable Sonar"],
        "Hunting & Shooting": ["Camo Hunting Blind Portable", "Binoculars 10x42 Waterproof", "Rangefinder Laser Hunting", "Shooting Ear Protection Muffs", "Game Bag Deer Processing", "Scent Eliminator Spray"],
        "Climbing": ["Climbing Chalk Bag with Belt", "Locking Carabiner Screwgate", "Bouldering Crash Pad", "Climbing Harness Adjustable", "Hangboard Training Grip", "Dynamic Climbing Rope 60m"],
        "Winter Sports": ["Ski Goggles Anti Fog UV", "Snowboard Bindings All Mountain", "Thermal Base Layer Set Merino", "Snowshoes with Poles", "Heated Gloves Rechargeable", "Ski Boot Bag Backpack"],
        "Outdoor Lighting & Power": ["Rechargeable LED Headlamp", "Solar Camping Lantern Collapsible", "Tactical Flashlight High Lumen", "Portable Solar Charger Camping", "Camp Light String USB", "Waterproof Power Bank Rugged"],
    },
    "Automotive": {
        "Car Interior Accessories": ["Car Seat Gap Filler Organizer", "Steering Wheel Cover Leather", "Car Trash Can Leak Proof", "Sun Shade Windshield Foldable", "Backseat Organizer Kick Mat", "Ambient LED Footwell Lights"],
        "Car Exterior & Care": ["Ceramic Coating Spray Detailer", "Microfiber Wash Mitt and Towels", "Foam Cannon Pressure Washer", "Headlight Restoration Kit", "Car Cover Waterproof Outdoor", "Wheel Cleaner Iron Remover"],
        "Car Electronics": ["Dash Cam Front and Rear 4K", "Bluetooth FM Transmitter Car", "Wireless CarPlay Adapter", "Tire Pressure Monitoring System", "OBD2 Scanner Bluetooth", "Backup Camera Wireless Kit"],
        "Motorcycle Gear": ["Full Face Motorcycle Helmet DOT", "Textile Riding Jacket Armored", "Motorcycle Gloves Touchscreen", "Tank Bag Magnetic", "Bluetooth Helmet Intercom", "Motorcycle Cover Waterproof"],
        "Tires & Wheels": ["Portable Air Compressor 12V", "Tire Inflator with Gauge Digital", "Wheel Lock Lug Nut Set", "Tire Repair Plug Kit", "Hubcap Set 16 inch", "Snow Chains Tire Traction"],
        "Car Tools & Emergency": ["Jump Starter Power Pack 2000A", "Roadside Emergency Kit Bag", "Hydraulic Floor Jack 3 Ton", "Socket Wrench Set Mechanics", "Window Breaker Seatbelt Cutter", "Tow Strap Heavy Duty Recovery"],
        "Truck & Off-Road": ["Truck Bed Tonneau Cover", "Roof Rack Cross Bars Universal", "LED Light Bar Off Road", "Winch Synthetic Rope 12000lb", "Mud Flaps Splash Guards", "Bed Liner Spray On Kit"],
        "EV & Fuel Accessories": ["EV Charging Cable Type 2", "Portable EV Charger Level 2", "Fuel Injector Cleaner Additive", "Jerry Can Fuel Container", "Battery Trickle Charger Maintainer", "Charging Cable Holder Wall Mount"],
    },
    "Tools & DIY": {
        "Hand Tools": ["Ratcheting Screwdriver Set", "Adjustable Wrench Set Chrome", "Precision Screwdriver Kit Electronics", "Claw Hammer Fiberglass Handle", "Utility Knife Retractable Blades", "Locking Pliers Vise Grip Set"],
        "Power Tools": ["Cordless Drill Driver 20V Kit", "Orbital Sander Variable Speed", "Angle Grinder 4.5 inch", "Jigsaw with Laser Guide", "Impact Driver Brushless", "Oscillating Multi Tool Kit"],
        "Measuring & Layout": ["Laser Distance Measure 100ft", "Digital Caliper Stainless", "Self Leveling Cross Line Laser", "Stud Finder Wall Scanner", "Tape Measure Magnetic Hook", "Digital Angle Finder Protractor"],
        "Workshop Storage": ["Rolling Tool Chest Cabinet", "Pegboard Organizer Kit", "Magnetic Tool Holder Strip", "Parts Organizer Bin Rack", "Tool Bag Heavy Duty Wide Mouth", "Workbench with Vise"],
        "Fasteners & Hardware": ["Assorted Screw Set with Case", "Wall Anchors Drywall Kit", "Hex Bolt and Nut Assortment", "Zip Ties Heavy Duty Pack", "Cabinet Hinges Soft Close", "Furniture Legs Set Metal"],
        "Painting & Finishing": ["Paint Roller Kit with Tray", "HVLP Paint Sprayer Electric", "Painters Tape Multi Surface", "Drop Cloth Canvas Heavy", "Wood Stain Gel Interior", "Epoxy Resin Kit Clear Casting"],
        "Safety Equipment": ["Safety Glasses Anti Fog Pack", "Work Gloves Cut Resistant", "Respirator Mask with Filters", "Ear Muffs Noise Reduction", "Knee Pads Gel Construction", "Reflective Safety Vest Class 2"],
        "Plumbing & Electrical": ["Pipe Wrench Heavy Duty", "Wire Stripper Crimper Tool", "Multimeter Digital Auto Ranging", "Drain Snake Auger Cordless", "Heat Shrink Tubing Kit", "Voltage Tester Non Contact", "Fish Tape Conduit Wire Puller", "Cable Pulling Rods Kit"],
    },
    "Office & Stationery": {
        "Notebooks & Journals": ["Dotted Bullet Journal Hardcover", "Leather Refillable Travel Notebook", "Spiral Notebook College Ruled", "Gratitude Journal Guided Prompts", "Sketchbook Mixed Media", "Pocket Notebook 3 Pack"],
        "Pens & Writing": ["Fountain Pen Set with Ink", "Gel Pen Set Fine Point", "Fineliner Pen Set 24 Colors", "Mechanical Pencil 0.5mm Set", "Calligraphy Brush Pen Set", "Erasable Pen Refills"],
        "Planners & Calendars": ["Undated Weekly Planner", "Desk Pad Calendar Monthly", "Academic Planner Student", "Wall Calendar Dry Erase", "Habit Tracker Notepad", "Meal Planning Pad Magnetic"],
        "Desk Organization": ["Bamboo Desk Organizer Caddy", "Cable Management Tray Under Desk", "Acrylic File Sorter Vertical", "Desk Mat Leather Large", "Pen Holder Rotating Storage", "Drawer Organizer Office Tray"],
        "Paper & Filing": ["Manila File Folders Letter Size", "Sheet Protectors Heavyweight", "Ring Binder 3 inch D Ring", "Printer Paper Bright White Ream", "Index Card Dividers Tabs", "Document Storage Box Fireproof"],
        "Labels & Shipping": ["Thermal Label Printer 4x6", "Shipping Label Sticker Sheets", "Poly Mailer Bags Self Seal", "Bubble Mailer Padded Envelopes", "Packing Tape Dispenser Gun", "Barcode Scanner Wireless"],
        "Art & Presentation": ["Whiteboard Magnetic Dry Erase", "Cork Board Bulletin Framed", "Easel Pad Flip Chart", "Laser Pointer Presentation Remote", "Poster Frame Snap Aluminum", "Portfolio Case Zippered"],
        "Office Electronics": ["Paper Shredder Cross Cut", "Electric Stapler Heavy Duty", "Laminator Machine Thermal", "Label Maker Wireless Bluetooth", "Desktop Calculator 12 Digit", "Time Clock Punch Machine"],
    },
    "Arts & Crafts": {
        "Painting Supplies": ["Acrylic Paint Set 24 Colors", "Watercolor Pan Set Portable", "Canvas Panels Pack 8x10", "Paint Brush Set Synthetic", "Gouache Paint Jelly Cup Set", "Palette Knife Set Stainless"],
        "Drawing & Illustration": ["Graphite Pencil Set Sketching", "Alcohol Marker Set Dual Tip", "Colored Pencils 72 Set Tin", "Blending Stump and Eraser Kit", "Charcoal Drawing Set", "Light Pad Tracing Board A4"],
        "Sewing & Textiles": ["Sewing Machine Beginner 12 Stitch", "Fabric Quarter Bundle Cotton", "Embroidery Starter Kit Hoop", "Sewing Thread Set 60 Spools", "Rotary Cutter and Mat Set", "Pin Cushion Magnetic Tray"],
        "Knitting & Crochet": ["Crochet Hook Set Ergonomic", "Chunky Merino Wool Yarn", "Interchangeable Knitting Needle Set", "Amigurumi Kit Beginner", "Yarn Winder and Swift", "Stitch Marker Set Locking"],
        "Jewelry Making": ["Beading Wire and Crimp Kit", "Polymer Clay Set 50 Colors", "Resin Jewelry Mold Set", "Jump Ring Assortment Box", "Jewelry Pliers Set 3 Piece", "Charm Pendant Assortment Mixed"],
        "Paper Crafts": ["Die Cutting Machine Starter", "Cardstock Paper Pack Colored", "Scrapbook Album Refillable", "Washi Tape Set Decorative", "Origami Paper Double Sided", "Quilling Paper Strips Kit", "Vinyl Sticker Pack Die Cut", "Laptop Sticker Set Waterproof"],
        "Candle & Soap Making": ["Soy Wax Flakes 10lb", "Candle Wick and Sticker Kit", "Fragrance Oil Set for Candles", "Silicone Soap Mold Loaf", "Melt and Pour Soap Base", "Candle Tins with Lids Bulk"],
        "Craft Tools & Storage": ["Hot Glue Gun with Sticks", "Craft Storage Cart Rolling", "Cutting Mat Self Healing A2", "Heat Press Machine Small", "Vinyl Weeding Tool Set", "Bead Organizer Case Compartments"],
    },
    "Food & Beverage": {
        "Coffee & Tea": ["Single Origin Whole Bean Coffee", "Pour Over Coffee Dripper Set", "Loose Leaf Tea Sampler Tin", "Cold Brew Coffee Concentrate", "Matcha Green Tea Powder Ceremonial", "French Press Double Wall"],
        "Snacks & Confectionery": ["Artisan Chocolate Bar Set", "Gourmet Popcorn Variety Pack", "Freeze Dried Fruit Snacks", "Protein Cookie Box", "Trail Mix Bulk Bag", "Handmade Caramel Sea Salt"],
        "Pantry & Condiments": ["Extra Virgin Olive Oil Cold Pressed", "Hot Sauce Gift Set", "Aged Balsamic Vinegar", "Truffle Oil Infused", "Artisan Pasta Bronze Cut", "Raw Honey Unfiltered Jar"],
        "Spices & Seasoning": ["Global Spice Blend Gift Set", "Smoked Paprika Sweet", "Everything Bagel Seasoning", "Whole Peppercorn Grinder", "Curry Powder Authentic Blend", "Chili Crisp Crunchy Oil"],
        "Health Foods & Superfoods": ["Organic Spirulina Powder", "Chia Seeds Bulk Organic", "Plant Based Protein Powder Vanilla", "Apple Cider Vinegar Gummies", "MCT Oil Coconut Derived", "Adaptogen Mushroom Coffee Blend"],
        "Beverages & Mixers": ["Sparkling Water Flavor Drops", "Cocktail Syrup Set Bar", "Kombucha Brewing Starter Kit", "Electrolyte Hydration Packets", "Instant Boba Milk Tea Kit", "Non Alcoholic Aperitif"],
        "Baking Ingredients": ["Gluten Free Flour Blend", "Vanilla Bean Paste Madagascar", "Cocoa Powder Dutch Process", "Sprinkles Mix Assortment", "Baking Yeast Instant Dry", "Sourdough Starter Culture"],
        "Gift Baskets & Sets": ["Gourmet Charcuterie Gift Box", "Coffee Lovers Gift Set", "Hot Chocolate Bomb Assortment", "Tea and Honey Gift Basket", "Snack Care Package Box", "Wine and Cheese Pairing Set"],
    },
    "Party & Occasions": {
        "Party Decorations": ["Balloon Arch Garland Kit", "Birthday Banner Personalized", "Table Confetti Metallic", "Paper Lantern Party Set", "Photo Booth Props Set", "Fringe Curtain Backdrop"],
        "Tableware & Disposables": ["Disposable Plates Palm Leaf", "Party Cups with Lids and Straws", "Cake Topper Acrylic Custom", "Napkins Cocktail Printed", "Cupcake Liners and Toppers", "Charcuterie Board Disposable"],
        "Wedding Supplies": ["Wedding Guest Book Rustic", "Bridesmaid Proposal Box", "Wedding Favor Boxes Bulk", "Ring Bearer Pillow Box", "Aisle Runner Fabric", "Wedding Sign Acrylic Welcome"],
        "Gift Wrap & Cards": ["Kraft Wrapping Paper Roll", "Greeting Card Assortment Box", "Gift Bags Assorted Sizes", "Ribbon and Bow Set", "Custom Thank You Cards", "Gift Box with Magnetic Lid"],
        "Costumes & Dress Up": ["Halloween Costume Adult", "Kids Superhero Cape Set", "Animal Onesie Pajama Costume", "Masquerade Mask Venetian", "Wig Cosplay Heat Resistant", "Face Paint Kit Non Toxic"],
        "Seasonal & Holiday": ["Christmas Ornament Set Shatterproof", "Advent Calendar Fillable", "Halloween Inflatable Yard Decor", "Easter Egg Decorating Kit", "Thanksgiving Table Runner", "Holiday Stocking Personalized"],
        "Balloons & Novelty": ["Number Foil Balloon 40 inch", "Confetti Latex Balloons Bulk", "Helium Tank Disposable", "LED Balloon Lights", "Bubble Balloon Clear Stuffing", "Balloon Weight Set Decorative"],
        "Event Rentals & Signage": ["Chalkboard Easel Sign", "Table Number Holders Set", "Card Box Wedding Lockable", "Seating Chart Display Board", "String Light Backdrop Stand", "Portable Folding Table Cover"],
    },
    "Books & Media": {
        "Fiction & Literature": ["Contemporary Romance Paperback Novel", "Fantasy Series Boxed Set", "Thriller Mystery Hardcover", "Short Story Collection", "Classic Literature Clothbound Edition", "Sci Fi Space Opera Novel"],
        "Non-Fiction & Self Help": ["Productivity Habits Hardcover Book", "Personal Finance Beginners Guide", "Mindfulness Meditation Workbook", "Business Strategy Bestseller", "Memoir Hardcover Signed", "Popular Science Paperback"],
        "Cookbooks": ["Mediterranean Diet Cookbook", "Air Fryer Recipe Book", "Sourdough Baking Guide", "Vegan Meal Prep Cookbook", "Cocktail Recipe Book Illustrated", "Regional Cuisine Hardcover"],
        "Children's Books": ["Board Book Set for Toddlers", "Bedtime Story Picture Book", "Early Reader Chapter Book Set", "Interactive Lift the Flap Book", "Personalized Childrens Storybook", "Activity Book with Stickers"],
        "Comics & Manga": ["Manga Volume Boxed Set", "Graphic Novel Hardcover", "Comic Book Storage Boxes", "Webcomic Print Collection", "Indie Comic Zine", "Art Book Illustrated Companion"],
        "Educational & Reference": ["Language Learning Workbook", "Test Prep Study Guide", "Atlas World Map Book", "Field Guide to Birds", "Dictionary and Thesaurus Set", "Coding Textbook Beginners"],
        "Music & Vinyl": ["Vinyl Record LP Album", "Turntable Belt Drive Bluetooth", "Vinyl Storage Crate Wood", "Record Cleaning Brush Kit", "Cassette Tape Album", "CD Album Deluxe Edition"],
        "Games & Film Media": ["Blu-ray Collector Edition Film", "Documentary DVD Box Set", "Video Game Physical Edition", "Movie Poster Reproduction Print", "Soundtrack Vinyl Limited", "Board Game Expansion Pack"],
    },
    "Digital Products": {
        "Templates & Printables": ["Printable Wall Art Digital Download", "Canva Instagram Template Pack", "Resume Template Editable Word", "Budget Spreadsheet Excel Template", "Wedding Invitation Template Printable", "Notion Planner Template"],
        "Fonts & Graphics": ["Handwritten Script Font Bundle", "SVG Cut File Bundle Cricut", "Procreate Brush Pack", "Lightroom Preset Mobile Pack", "Clipart Illustration Bundle PNG", "Seamless Pattern Digital Paper"],
        "Courses & Ebooks": ["Online Course Video Bundle", "Meal Plan Ebook PDF", "Photography Guide Ebook", "Business Startup Workbook Digital", "Fitness Program 12 Week PDF", "Language Phrasebook Digital"],
        "Audio & Music Files": ["Royalty Free Music Pack", "Guided Meditation Audio Download", "Sound Effects Library Digital", "Sample Pack Drum Loops", "Podcast Intro Music Track", "Binaural Sleep Audio Album"],
        "Software & Plugins": ["Photoshop Action Set", "Shopify Theme Digital License", "Excel Macro Add In", "VST Audio Plugin", "Mobile App Lifetime License", "Browser Extension Pro Key"],
        "Gaming Digital Goods": ["Game Key Digital Code", "Twitch Overlay Stream Pack", "Discord Server Template", "VTuber Avatar Model", "Minecraft Texture Pack", "Roblox Game Pass Code"],
        "Gift Cards & Credits": ["Digital Gift Card Store Credit", "eGift Voucher Instant Delivery", "Membership Access Pass Digital", "Subscription Renewal Code", "Workshop Ticket Digital", "Consultation Booking Voucher"],
        "Stock Media": ["Stock Photo Bundle Commercial", "Stock Video Footage Pack", "3D Model Asset Pack", "Mockup PSD Bundle", "Icon Set Vector SVG", "Texture Pack High Resolution"],
    },
    "Industrial & Business Supplies": {
        "Packaging & Shipping Supplies": ["Corrugated Shipping Boxes Bulk", "Stretch Wrap Pallet Film", "Void Fill Packing Paper", "Custom Printed Tissue Paper", "Kraft Mailer Boxes Wholesale", "Strapping Band Tensioner Kit"],
        "Retail & Display Fixtures": ["Clothing Rack Rolling Garment", "Acrylic Display Riser Set", "Slatwall Panel Hooks", "Mannequin Dress Form Adjustable", "Countertop Display Case Locking", "Price Tag Gun with Labels"],
        "Restaurant & Food Service": ["Commercial Food Prep Containers", "Chafing Dish Buffet Set", "Restaurant Menu Covers", "Disposable Takeout Containers Bulk", "Commercial Cutting Board Set", "Ice Bucket with Tongs Insulated"],
        "Janitorial & Sanitation": ["Commercial Floor Mop Bucket", "Bulk Trash Liners 55 Gallon", "Hand Sanitizer Dispenser Stand", "Wet Floor Caution Sign", "Industrial Degreaser Concentrate", "Restroom Paper Towel Dispenser"],
        "Warehouse Equipment": ["Hand Truck Dolly Convertible", "Pallet Jack Manual 5500lb", "Wire Shelving Unit Chrome", "Platform Cart Folding", "Anti Fatigue Floor Mat", "Storage Bin Stackable Industrial"],
        "Lab & Measurement": ["Digital pH Meter Tester", "Lab Beaker Glass Set", "Precision Analytical Balance Scale", "Nitrile Exam Gloves Box", "Infrared Thermometer Gun Industrial", "Microscope Slide Set Prepared"],
        "Signage & Safety": ["Custom Vinyl Banner Printed", "Exit Sign LED Emergency", "Floor Marking Tape Safety", "First Aid Kit OSHA Compliant", "Fire Extinguisher Bracket Mount", "Traffic Cone Set Reflective"],
        "Print & Promotional": ["Custom Embroidered Logo Cap", "Branded Tote Bag Bulk", "Promotional Pen Custom Print", "Business Card Printing Premium", "Sticker Roll Custom Die Cut", "Trade Show Table Cover Printed"],
    },
    "Spiritual & Metaphysical": {
        "Crystals & Stones": ["Amethyst Cluster Raw Crystal", "Rose Quartz Tumbled Stones", "Crystal Grid Set with Chart", "Selenite Charging Plate", "Obsidian Sphere Polished", "Chakra Stone Set Pouch"],
        "Tarot & Divination": ["Tarot Deck with Guidebook", "Oracle Card Deck Illustrated", "Pendulum Crystal Dowsing", "Rune Stone Set Wooden", "Scrying Mirror Black Obsidian", "Tarot Cloth and Storage Box"],
        "Incense & Smudging": ["White Sage Smudge Stick Bundle", "Palo Santo Sticks Sustainable", "Incense Cone Backflow Burner", "Resin Incense Charcoal Set", "Herbal Smudge Kit with Feather", "Incense Stick Holder Wooden"],
        "Altar & Ritual Supplies": ["Ritual Candle Set Colored", "Brass Altar Bell", "Offering Bowl Ceramic", "Book of Shadows Journal", "Altar Cloth Velvet Embroidered", "Cauldron Cast Iron Small"],
        "Meditation & Sound": ["Tibetan Singing Bowl Set", "Meditation Chime Bell", "Mala Beads 108 Sandalwood", "Sound Healing Tuning Fork", "Zen Sand Garden Desktop", "Chakra Sound Bath CD"],
        "Astrology & Zodiac": ["Zodiac Constellation Necklace", "Birth Chart Print Personalized", "Astrology Guidebook Illustrated", "Moon Phase Wall Hanging", "Zodiac Candle Sign Specific", "Celestial Tapestry Wall Art"],
        "Herbal & Botanical": ["Dried Herb Apothecary Set", "Herbal Tea Ritual Blend", "Flower Essence Dropper", "Botanical Spell Jar Kit", "Loose Herb Storage Jars Labeled", "Mortar and Pestle Marble"],
        "Spiritual Decor": ["Buddha Statue Meditation", "Hamsa Hand Wall Hanging", "Sun and Moon Mirror Decor", "Tree of Life Wall Art Metal", "Evil Eye Hanging Ornament", "Sacred Geometry Wooden Art"],
    },
}

UNCATEGORIZED = "uncategorized"


def categories() -> list[str]:
    return list(TAXONOMY.keys())


def niches() -> list[tuple[str, str]]:
    """[(kategori, nis), ...] duz liste - vektor sirasiyla ayni."""
    return [(cat, niche) for cat, group in TAXONOMY.items() for niche in group]


def examples() -> list[list[str]]:
    """niches() ile ayni sirada ornek baslik listeleri."""
    return [titles for group in TAXONOMY.values() for titles in group.values()]


def summary() -> str:
    n_cat = len(TAXONOMY)
    n_niche = sum(len(g) for g in TAXONOMY.values())
    n_ex = sum(len(t) for g in TAXONOMY.values() for t in g.values())
    return f"{n_cat} kategori, {n_niche} nis, {n_ex} ornek baslik"


if __name__ == "__main__":
    print(summary())
