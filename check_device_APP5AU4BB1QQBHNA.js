#!/usr/bin/env node
/**
 * Check device APP5AU4BB1QQBHNA status and info
 */

const { AK, SK, HOST, SVC, CT, SHD, hmacSign, api, P } = require('./shared/vmos_api');

const PAD = 'APP5AU4BB1QQBHNA';

async function main() {
  console.log('═'.repeat(70));
  console.log(`  DEVICE STATUS CHECK: ${PAD}`);
  console.log('═'.repeat(70));

  // Try to get device info
  console.log('\n▶ GET DEVICE INFO');
  const info = await api('/vcpcloud/api/padApi/getPadInfo', { padCode: PAD });
  console.log(JSON.stringify(info, null, 2));

  // Try to list all devices
  console.log('\n▶ LIST ALL DEVICES');
  const list = await api('/vcpcloud/api/padApi/queryPadList', { pageNum: 1, pageSize: 100 });
  if (list.code === 200 && list.data && list.data.list) {
    console.log(`Total devices: ${list.data.list.length}`);
    console.log('\nDevice list:');
    list.data.list.forEach(d => {
      console.log(`  - ${d.padCode} | ${d.deviceName || 'unnamed'} | status: ${d.status || 'unknown'}`);
    });
  } else {
    console.log('Failed to list devices:', list);
  }

  console.log('\n' + '═'.repeat(70));
}

main().catch(console.error);
