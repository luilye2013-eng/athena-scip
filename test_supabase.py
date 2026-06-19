from supabase import create_client

url = "https://catpprgdbvenutyyjqbx.supabase.co"
key = "sb_publishable_ykiqckKEQw2m8XXvX4cGnQ_5ijzb7Py"

print("Testing Supabase connection...")
try:
    client = create_client(url, key)
    print("✅ Supabase client created successfully!")
    
    # Test a simple query
    response = client.table("events").select("id", count="exact").limit(1).execute()
    print(f"✅ Query successful! Found {response.count} events.")
    
except Exception as e:
    print(f"❌ Error: {e}")