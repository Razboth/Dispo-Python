# MongoDB Database Setup Guide for Dispo-Python

## ✅ Database Setup Complete!

Your MongoDB database has been successfully installed and configured. Here's what was set up:

### 📊 Database Information
- **Database Name**: `disposisi`
- **Host**: `localhost`
- **Port**: `27017`
- **Status**: ✅ Running

### 📁 Collections Created
- `documents` - Main document storage
- `users` - User accounts and authentication
- `templates` - Document templates
- `audit_log` - Audit trail for all actions
- `counters` - Auto-increment counters
- `notifications` - User notifications
- `workflow` - Document workflow states
- `document_versions` - Version history
- `fs.files` & `fs.chunks` - GridFS for file storage

### 👤 Default Admin Account
- **Username**: `admin`
- **Password**: `Admin@123`
- **Email**: `admin@disposisi.local`
- **Role**: Administrator

⚠️ **IMPORTANT**: Please change the admin password immediately after first login!

## 🚀 Quick Start Commands

### Start MongoDB Service
```bash
# macOS
brew services start mongodb-community

# Check status
brew services list | grep mongodb

# Stop service
brew services stop mongodb-community
```

### Access MongoDB Shell
```bash
# Connect to MongoDB
mongosh

# Select database
use disposisi

# Show collections
show collections

# Count documents
db.documents.countDocuments()
```

### Initialize/Reset Database
```bash
# Using the run script
./run.sh init

# Or directly
source venv_new/bin/activate
python src/scripts/init_db.py

# With custom settings
python src/scripts/init_db.py --host localhost --port 27017 --database disposisi
```

### Backup Database
```bash
# Using run script
./run.sh backup

# Or using mongodump directly
mongodump --db disposisi --out backups/backup_$(date +%Y%m%d_%H%M%S)
```

### Restore Database
```bash
# Using run script
./run.sh restore backups/backup_20240101_120000

# Or using mongorestore
mongorestore --db disposisi --drop backups/backup_20240101_120000/disposisi
```

## 🔧 Configuration

The database configuration is stored in `config.ini`:

```ini
[DATABASE]
host = localhost
port = 27017
database = disposisi
```

To use a remote MongoDB server, update these values accordingly.

## 📝 Common MongoDB Commands

### User Management
```javascript
// Create a new database user
use disposisi
db.createUser({
  user: "disposisi_user",
  pwd: "secure_password",
  roles: [
    { role: "readWrite", db: "disposisi" }
  ]
})

// List users
db.getUsers()
```

### Document Operations
```javascript
// Find all documents
db.documents.find()

// Find documents by type
db.documents.find({ jenis_dokumen: "Surat Masuk" })

// Count documents by status
db.documents.aggregate([
  { $group: { _id: "$status", count: { $sum: 1 } } }
])
```

### Database Maintenance
```javascript
// Check database size
db.stats()

// Check collection statistics
db.documents.stats()

// Rebuild indexes
db.documents.reIndex()

// Compact collection
db.runCommand({ compact: 'documents' })
```

## 🛠️ Troubleshooting

### MongoDB Won't Start
```bash
# Check if MongoDB is already running
ps aux | grep mongod

# Check logs
tail -f /opt/homebrew/var/log/mongodb/mongo.log

# Try starting manually
mongod --dbpath /opt/homebrew/var/mongodb
```

### Connection Issues
```bash
# Test connection
mongosh --eval "db.version()"

# Check if port is open
lsof -i :27017

# Check MongoDB status
brew services list | grep mongodb
```

### Permission Issues
```bash
# Fix permissions on data directory
sudo chown -R $(whoami) /opt/homebrew/var/mongodb
sudo chmod -R 755 /opt/homebrew/var/mongodb
```

### Reset Everything
```bash
# Stop MongoDB
brew services stop mongodb-community

# Remove data (CAUTION: This deletes all data!)
rm -rf /opt/homebrew/var/mongodb/*

# Start MongoDB
brew services start mongodb-community

# Reinitialize database
./run.sh init
```

## 📊 MongoDB GUI Tools

For easier database management, you can use these GUI tools:

1. **MongoDB Compass** (Official)
   ```bash
   brew install --cask mongodb-compass
   ```
   Connection string: `mongodb://localhost:27017/disposisi`

2. **Studio 3T**
   ```bash
   brew install --cask studio-3t
   ```

3. **Robo 3T**
   ```bash
   brew install --cask robo-3t
   ```

## 🔒 Security Recommendations

1. **Enable Authentication**
   ```javascript
   // In mongosh
   use admin
   db.createUser({
     user: "admin",
     pwd: "secure_admin_password",
     roles: [ { role: "root", db: "admin" } ]
   })
   ```

2. **Create Application User**
   ```javascript
   use disposisi
   db.createUser({
     user: "disposisi_app",
     pwd: "app_password",
     roles: [ { role: "readWrite", db: "disposisi" } ]
   })
   ```

3. **Update config.ini**
   ```ini
   [DATABASE]
   host = localhost
   port = 27017
   database = disposisi
   username = disposisi_app
   password = app_password
   auth_source = disposisi
   ```

4. **Enable SSL/TLS** (for production)
   - Generate SSL certificates
   - Configure MongoDB with SSL
   - Update application config

## 📈 Monitoring

Check database health:
```bash
# Database statistics
mongosh disposisi --eval "db.stats()"

# Collection statistics
mongosh disposisi --eval "db.documents.stats()"

# Current operations
mongosh disposisi --eval "db.currentOp()"

# Server status
mongosh admin --eval "db.serverStatus()"
```

## 🆘 Support

If you encounter any issues:

1. Check MongoDB logs: `/opt/homebrew/var/log/mongodb/mongo.log`
2. Verify MongoDB is running: `brew services list`
3. Test connection: `mongosh --eval "db.version()"`
4. Check application logs: `logs/application.log`

Your MongoDB database is now fully configured and ready to use with the Dispo-Python application!