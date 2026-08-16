with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora frontend\\src\\App.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Add companion integration area before the closing div
old_end = '''      </div>
    </>'''

new_end = '''      </div>

      {/* Character Integration - Companion area at the center */}
      <div className="relative z-10 pt-8 pb-12">
        {/* Companion position - elevated but not dominating */}
        <div className="absolute -inset-0 overflow-hidden pointer-events-none">
          {/* Subtle background glow for ambiance */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-[#60a5fa] opacity-5 blur-3xl translate-y-20 md:translate-y-0 transition-y-200 md:translate-y-0" />
          <div className="absolute bottom-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] rounded-full bg-[#60a5fa] opacity-5 blur-3xl translate-y-20 md:translate-y-0 transition-y-200 md:translate-y-0" />
        </div>
      </div>
    </>'''

if old_end in content:
    content = content.replace(old_end, new_end)
    print('Added companion integration area')
else:
    print('Old end pattern not found')

with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora frontend\\src\\App.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("App.tsx redesigned")