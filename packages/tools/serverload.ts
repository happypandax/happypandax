import Client, { JsonArray, JsonMap } from 'happypandax-client';
import { hrtime } from 'process';

const SERVER = {
  port: 7008,
  host: 'localhost',
};

function elapsedTime(start: any, note: string) {
  var precision = 3; // 3 decimal places
  var elapsed = hrtime(start)[1] / 1000000; // divide by a million to get nano to milli
  console.log(
    hrtime(start)[0] + ' s, ' + elapsed.toFixed(precision) + ' ms - ' + note
  ); // print message + time
}

class HPX {
  client: Client;

  constructor(session_id?: string) {
    this.client = new Client({ name: 'tools', session_id });
  }

  async connect(host: string, port: number) {
    await this.client.connect({ host, port });
    await this.client.handshake({ user: null, password: null });
  }

  async call(msg: JsonArray) {
    const s = hrtime();
    const r = await this.client.send(msg);
    elapsedTime(s, JSON.stringify(msg));
  }

  async measureVarious(
    functions = [['library_view', { search_query: '', view_filter: null }]] as [
      [string, JsonMap]
    ]
  ) {
    for (const f of functions) {
      console.log(`Measuring ${f[1]}...`);
      await this.call([{ fname: f[0], ...f[1] }]);
    }
  }
}

export async function main() {
  const hpx = new HPX();
  await hpx.connect(SERVER.host, SERVER.port);
  await hpx.measureVarious();
}
