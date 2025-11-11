# MongoDB Atlas Setup Guide for AMMINA Platform

This guide walks you through setting up a **free MongoDB Atlas cluster** for the AMMINA platform.

## Why MongoDB Atlas?

- ✅ **Free tier** - 512MB storage forever (no credit card required)
- ✅ **Managed service** - No server maintenance needed
- ✅ **Cloud-based** - Access from anywhere
- ✅ **Automatic backups** - Data protection included
- ✅ **Global availability** - Choose your region
- ✅ **Perfect for Render/Fly.io/Railway** - Works with all cloud platforms

## Step-by-Step Setup (5-10 minutes)

### Step 1: Create MongoDB Atlas Account

1. Go to [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Click **"Try Free"** or **"Sign Up"**
3. Register with:
   - Email and password, OR
   - Google account, OR
   - GitHub account
4. Complete email verification if required
5. **No credit card needed** for free tier!

### Step 2: Create Your First Cluster

1. After logging in, you'll see **"Create a deployment"** or **"Build a Database"**
2. Click to start cluster creation

3. **Choose Deployment Type**:
   - Select **"M0 Free"** tier
   - This provides:
     - 512MB storage
     - Shared RAM
     - Shared vCPU
     - No backup (manual export recommended)

4. **Select Cloud Provider & Region**:
   - **Provider**: AWS, Google Cloud, or Azure (all work fine)
   - **Region**: Choose closest to where your Render app will be deployed
     - For Render Oregon: Choose `us-west-2` (AWS) or similar
     - For Render Frankfurt: Choose `eu-central-1` or similar
     - For other providers: Choose geographically close regions

5. **Cluster Name**:
   - Default: `Cluster0` (or customize to `ammina-db`)
   - Click **"Create Cluster"**

6. **Wait for cluster creation** (usually 1-3 minutes)
   - You'll see a progress indicator
   - Once ready, it will show "Active" status

### Step 3: Create Database User

**IMPORTANT**: This is NOT your Atlas login - it's a separate database user for your application.

1. In the left sidebar, click **"Database Access"**
2. Click **"+ ADD NEW DATABASE USER"**
3. **Authentication Method**: Select **"Password"**
4. **Create credentials**:
   - **Username**: Choose a username (e.g., `ammina_user`)
   - **Password**: Click **"Autogenerate Secure Password"** or create your own
   - ⚠️ **SAVE THESE CREDENTIALS** - you'll need them for the connection string!

5. **Database User Privileges**:
   - Select **"Built-in Role"**: `Read and write to any database`
   - (This allows your app full access to create/modify collections)

6. **Temporary User** (optional): Leave unchecked for permanent access
7. Click **"Add User"**

### Step 4: Configure Network Access

By default, MongoDB Atlas blocks all connections for security. You need to allow Render (or your deployment platform) to connect.

1. In the left sidebar, click **"Network Access"**
2. Click **"+ ADD IP ADDRESS"**
3. **Configure Access**:
   - **Option A - Allow from Anywhere** (Recommended for cloud platforms):
     - Click **"ALLOW ACCESS FROM ANYWHERE"**
     - This adds `0.0.0.0/0` (all IPs)
     - ✅ Required for Render, Fly.io, Railway, etc.
     - ⚠️ Ensure strong database user password!

   - **Option B - Specific IPs** (More secure but complex):
     - Find your deployment platform's IP ranges
     - Add each IP/CIDR range manually
     - Not recommended for platforms with dynamic IPs

4. **Optional**: Add description like "Render deployment access"
5. Click **"Confirm"**

**Security Note**: With `0.0.0.0/0`, anyone can attempt connections, but they still need your username/password. Use a strong password!

### Step 5: Get Your Connection String

1. Go back to **"Database"** in the left sidebar
2. Find your cluster (e.g., `Cluster0`)
3. Click **"Connect"** button
4. Choose **"Connect your application"**
5. **Driver & Version**:
   - Driver: **Python**
   - Version: **3.12 or later** (or select latest)

6. **Copy the connection string** - it looks like:
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

7. **Replace placeholders**:
   - Replace `<username>` with your database username
   - Replace `<password>` with your database password
   - **IMPORTANT**: URL-encode special characters in password if any
     - Example: `p@ssw0rd!` becomes `p%40ssw0rd%21`
     - Use online URL encoder if needed

8. **Final connection string example**:
   ```
   mongodb+srv://ammina_user:MySecurePass123@cluster0.abc123.mongodb.net/ammina_platform?retryWrites=true&w=majority
   ```

### Step 6: Set Connection String in Render

1. Go to your Render Dashboard
2. Open your web service
3. Navigate to **"Environment"** tab
4. Find or add `MONGODB_URI` variable
5. Paste your complete connection string
6. Click **"Save Changes"**
7. Render will automatically redeploy with the new variable

### Step 7: Verify Connection (Optional but Recommended)

After deploying your app on Render:

1. Check Render logs for successful database connection
   - Look for messages like "Connected to MongoDB successfully"
   - Or absence of MongoDB connection errors

2. Test in your application:
   - Try registering a new user
   - If successful, your MongoDB connection works!

3. View data in Atlas:
   - Go to "Database" → "Browse Collections"
   - You should see `ammina_platform` database
   - With collections like `users`, `datasets`, etc.

## Database Structure

Once your app is running, MongoDB Atlas will automatically create:

### Database: `ammina_platform`

**Collections Created by Application**:

1. **`users`** - User accounts and authentication
   ```json
   {
     "_id": ObjectId("..."),
     "username": "john_doe",
     "email": "john@example.com",
     "password_hash": "...",
     "is_admin": false,
     "created_at": ISODate("2024-01-15T10:30:00Z")
   }
   ```

2. **`datasets`** - Uploaded CSV/Excel file data
   ```json
   {
     "_id": ObjectId("..."),
     "user_id": ObjectId("..."),
     "filename": "manufacturers.csv",
     "original_filename": "manufacturers.csv",
     "data": [...],  // Actual dataset rows
     "upload_date": ISODate("..."),
     "file_size": 1024000,
     "row_count": 150,
     "column_count": 12
   }
   ```

3. **`query_history`** - Natural language queries and results
   ```json
   {
     "_id": ObjectId("..."),
     "user_id": ObjectId("..."),
     "query": "Show me all manufacturers in Kenya",
     "datasets_used": ["manufacturers.csv"],
     "result": "...",
     "timestamp": ISODate("..."),
     "execution_time": 2.34
   }
   ```

## Monitoring & Management

### View Your Data

1. **Browse Collections**:
   - Database → Browse Collections
   - Navigate through your data visually
   - Edit documents manually if needed

2. **Run Queries**:
   - Use the built-in MongoDB query interface
   - Example: `{ "username": "john_doe" }`
   - Useful for debugging

### Monitor Usage

1. **Metrics Dashboard**:
   - Database → Metrics
   - View connection count, operations/sec, storage usage
   - Track if approaching free tier limits (512MB)

2. **Storage Limits**:
   - Free tier: 512MB total
   - If exceeded, you'll need to upgrade or clean old data
   - Monitor in "Database" → "Cluster" → "Metrics"

3. **Connection Limits**:
   - Free tier: 500 connections max
   - Usually sufficient for small-medium apps

### Backup Your Data

⚠️ Free tier does NOT include automatic backups!

**Manual Export Options**:

1. **Using MongoDB Compass** (GUI Tool):
   - Download [MongoDB Compass](https://www.mongodb.com/products/compass)
   - Connect using your connection string
   - Export collections to JSON/CSV

2. **Using mongodump** (CLI):
   ```bash
   mongodump --uri="mongodb+srv://user:pass@cluster.mongodb.net/ammina_platform"
   ```

3. **Schedule Regular Exports** (Recommended):
   - Set calendar reminder (weekly/monthly)
   - Export data manually via Compass or mongodump
   - Store backups securely

## Security Best Practices

### 1. Strong Database User Password
- Use 16+ characters
- Mix uppercase, lowercase, numbers, symbols
- Don't reuse passwords from other services
- Rotate periodically (every 3-6 months)

### 2. Environment Variables
- ✅ Store `MONGODB_URI` in Render environment variables
- ❌ Never commit connection strings to Git
- ❌ Never share connection strings publicly

### 3. Network Access
- If possible, restrict to specific IPs instead of `0.0.0.0/0`
- Regularly review Network Access rules
- Remove unused IP addresses

### 4. User Permissions
- Only grant necessary permissions
- Use separate users for different apps if needed
- Regularly audit database users

### 5. Enable Monitoring
- Set up Atlas alerts for unusual activity
- Monitor connection patterns
- Review access logs periodically

## Troubleshooting

### Connection Timeout Errors

**Symptoms**: `MongoServerSelectionTimeoutError`, `Connection timeout`

**Solutions**:
1. ✅ Verify Network Access allows `0.0.0.0/0`
2. ✅ Check connection string format is correct
3. ✅ Ensure cluster is "Active" (not paused)
4. ✅ Verify username/password are correct
5. ✅ Check for typos in environment variable

### Authentication Failed

**Symptoms**: `Authentication failed`, `Invalid credentials`

**Solutions**:
1. ✅ Confirm database username (not Atlas login email)
2. ✅ Verify password is correct
3. ✅ Check for special characters - URL encode them
4. ✅ Try resetting database user password in Atlas

### Database Not Found

**Symptoms**: Database doesn't appear in Atlas

**Solutions**:
1. ✅ Database is created automatically on first write
2. ✅ Register a user in your app to trigger creation
3. ✅ Check connection string includes database name
4. ✅ Verify app successfully connected (check logs)

### Storage Limit Reached

**Symptoms**: `Storage quota exceeded`, `Write failed`

**Solutions**:
1. ✅ Upgrade to M2 tier ($9/month for 2GB)
2. ✅ Delete old datasets/query history
3. ✅ Implement data retention policy in app
4. ✅ Archive old data and export

### Cluster Paused

**Symptoms**: Connections fail after inactivity

**Solutions**:
1. ✅ Free tier clusters auto-pause after 60 days inactivity
2. ✅ Resume cluster in Atlas dashboard
3. ✅ Make a connection to prevent future pausing

## Upgrading from Free Tier

When you outgrow the 512MB free tier:

### M2 Tier - $9/month
- 2GB storage
- 2GB RAM
- Shared vCPU
- Automated backups available

### M5 Tier - $25/month
- 5GB storage
- 2GB RAM
- Dedicated vCPU
- Continuous backups
- Point-in-time recovery

### Upgrade Process:
1. Database → Click your cluster
2. Click **"Edit Configuration"** or **"Modify"**
3. Select new tier
4. Click **"Apply Changes"**
5. Cluster will upgrade with zero downtime

## Alternative: Self-Hosted MongoDB

If you prefer not to use Atlas:

### Option 1: Docker Container (Local Development)
```bash
docker run -d -p 27017:27017 --name mongodb \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password \
  mongo:latest
```
Connection string: `mongodb://admin:password@localhost:27017/ammina_platform`

### Option 2: DigitalOcean Droplet
- Deploy MongoDB on a $6/month Droplet
- Requires manual server management
- Not recommended unless you have DevOps experience

### Option 3: MongoDB Cloud on other providers
- AWS DocumentDB (MongoDB-compatible)
- Azure Cosmos DB (MongoDB API)
- Usually more expensive than Atlas

## Support & Resources

- **Atlas Documentation**: [docs.atlas.mongodb.com](https://docs.atlas.mongodb.com)
- **MongoDB University**: Free courses at [university.mongodb.com](https://university.mongodb.com)
- **Community Forums**: [community.mongodb.com](https://community.mongodb.com)
- **Support**: Available in Atlas dashboard (paid tiers)

## Summary Checklist

Before deploying your app, ensure:

- [ ] MongoDB Atlas account created
- [ ] Free M0 cluster created and active
- [ ] Database user created with strong password
- [ ] Network access configured (0.0.0.0/0)
- [ ] Connection string obtained and tested
- [ ] `MONGODB_URI` set in Render environment variables
- [ ] Connection verified (user registration works)
- [ ] Data appears in Atlas "Browse Collections"
- [ ] Backup strategy planned (manual exports)

---

**Need Help?** Check the AMMINA platform logs in Render dashboard or MongoDB Atlas monitoring for detailed error messages.
