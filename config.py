from prod import PROD

if PROD == 1:
    db = "/var/DatapackHub/data.db"
    rules = "/var/DatapackHub/rules.txt"
    class github():
        client_id = "8a0527a3da5b002db8c9"
        client_secret = "c3dd98c1ed8acc65989824e70d61fd49cf60640d"
else:
    db = "data.db"
    rules = "rules.txt"
    class github():
        client_id = "cd983835f4e37148ba77"
        client_secret = "56414b10caf5394328730deba6b41a6f38bfee8f"
    
valid_tags = [
    "Adventure", 
    "Magic", 
    "Minecraft but", 
    "Cursed", 
    "World Generation", 
    "Tools / Equipment", 
    "German", 
    "Recipe", 
    "Quality of Life",
    "Items / Blocks",
    "Cosmetic",
    "Miscellaneous",
    "Utility",
    "Vanilla+"
]

valid_types = [
    "datapack"
]