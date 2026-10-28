print("Con pm25: " + db.lecturas.countDocuments({ "medicion.pm25": { $ne: null } }))
print("Con carros: " + db.lecturas.countDocuments({ "medicion.carros": { $ne: null } }))
print("Total: " + db.lecturas.countDocuments({}))
