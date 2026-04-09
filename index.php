<?php
$search = isset($_GET['search']) ? $_GET['search'] : '';
$cwd = getcwd();

// ── Helpers ──────────────────────────────────────────────────────────────────
function sortByMtimeDesc($a, $b) {
    $mb = @filemtime($b); if (!$mb) $mb = 0;
    $ma = @filemtime($a); if (!$ma) $ma = 0;
    if ($mb === $ma) return strcasecmp($a, $b);
    return $mb - $ma;
}
function is_plot($f) {
    return preg_match('/\.(png|jpe?g|gif|pdf)$/i', $f);
}
function matches_search($f, $search) {
    return empty($search) || stripos($f, $search) !== false;
}

$entries = glob('*', GLOB_NOSORT);
if (!$entries) $entries = array();

$subdirs = array_values(array_filter($entries, 'is_dir'));
usort($subdirs, 'sortByMtimeDesc');

$files = array_values(array_filter($entries, 'is_file'));
usort($files, 'sortByMtimeDesc');

// ROOT files
$rootFiles = array();
foreach ($files as $f) {
    if (preg_match('/\.root$/i', $f)) $rootFiles[] = $f;
}

// Image files (standalone, not part of a plot group)
$imageFiles = array();
foreach ($files as $f) {
    if (preg_match('/\.(png|jpe?g|jpg|gif|svg)$/i', $f) && matches_search($f, $search))
        $imageFiles[] = $f;
}

// PDF files
$pdfFiles = array();
foreach ($files as $f) {
    if (preg_match('/\.pdf$/i', $f) && matches_search($f, $search))
        $pdfFiles[] = $f;
}

// Selected ROOT file
$selectedRoot = '';
if (!empty($_GET['rootfile'])) {
    $candidate = basename($_GET['rootfile']);
    if (in_array($candidate, $rootFiles)) $selectedRoot = $candidate;
}
if (!$selectedRoot && !empty($rootFiles)) $selectedRoot = $rootFiles[0];
?>
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title><?php echo htmlspecialchars(basename($cwd)); ?></title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
  <style>
    body > .container-fluid { margin-top: 20px; padding: 0 20px; }
    .empty-text { font-style: italic; font-size: 0.9rem; }

    /* ── existing plot cards (png/pdf) ── */
    #plot-listing .card { margin: 5px; max-width: 240px; }
    .card-img-top {
      max-height: var(--plot-img-max-height, 180px);
      object-fit: contain;
    }

    /* ── ROOT histogram cards ── */
    .root-card { margin: 5px; width: var(--root-card-w, 340px); }
    .root-plot-wrap { position: relative; background: #111; }
    .root-plot-div  { width: 100%; height: var(--root-card-h, 300px); }
    .root-plot-status {
      position: absolute; inset: 0; display: flex;
      align-items: center; justify-content: center;
      font-size: .8rem; color: #888; pointer-events: none;
    }
    .root-card .card-header { cursor: pointer; }
    .root-card .card-header:hover { background: #f8d7da; }

    /* ── Fullscreen modal for JSROOT ── */
    #rootModal .modal-dialog { max-width: 96vw; margin: 2vh auto; }
    #rootModal .modal-content { height: 94vh; }
    #rootModal .modal-body { flex: 1; padding: 0; overflow: hidden; }
    #rootModalPlot { width: 100%; height: 100%; }

    /* ── image lightbox ── */
    #imgModal .modal-dialog { max-width: 92vw; }
    #imgModal img { max-width: 100%; max-height: 82vh; object-fit: contain; display: block; margin: auto; }

    /* ── PDF cards ── */
    .pdf-embed { width: 100%; height: 300px; border: none; display: block; }
  </style>
</head>
<body>

<!-- ── Navbar / breadcrumb ──────────────────────────────────────────────── -->
<nav class="navbar navbar-light bg-light border-bottom">
  <div class="d-flex align-items-center">
    <a href="/" class="text-decoration-none" style="color:blue;"><i class="bi bi-house-door"></i></a>
    <?php
      $uri   = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
      $parts = explode('/', trim($uri, '/'));
      $accum = '';
      foreach ($parts as $i => $part) {
          $accum .= '/' . $part;
          echo '<span class="mx-2">/</span>';
          if ($i < count($parts) - 1) {
              echo '<a href="' . htmlspecialchars($accum) . '" class="text-decoration-none" style="color:blue;">' . htmlspecialchars($part) . '</a>';
          } else {
              echo '<span class="fw-light" style="color:blue;">' . htmlspecialchars($part) . '</span>';
          }
      }
    ?>
  </div>
  <form class="d-flex" method="get">
    <?php if ($selectedRoot): ?>
    <input type="hidden" name="rootfile" value="<?php echo htmlspecialchars($selectedRoot); ?>">
    <?php endif; ?>
    <input class="form-control me-2" type="search" name="search" placeholder="Pattern(s)" value="<?php echo htmlspecialchars($search); ?>">
    <button class="btn btn-outline-success" type="submit">Search</button>
  </form>
</nav>

<div class="container-fluid">

  <!-- ── Directories ──────────────────────────────────────────────────────── -->
  <h5 class="mt-4">Directories</h5>
  <?php if (!empty($subdirs)): ?>
    <ul>
      <?php foreach ($subdirs as $dir): if (matches_search($dir, $search)): ?>
        <li><a href="<?php echo htmlspecialchars($dir); ?>"><?php echo htmlspecialchars($dir); ?></a></li>
      <?php endif; endforeach; ?>
    </ul>
  <?php else: ?>
    <p class="empty-text">No directories found.</p>
  <?php endif; ?>

  <!-- ── ROOT histograms (JSROOT) ─────────────────────────────────────────── -->
  <?php if ($selectedRoot): ?>
  <h5 class="mt-4">
    ROOT histograms
    <?php if (count($rootFiles) > 1): ?>
    &mdash;
    <form method="get" style="display:inline">
      <?php if ($search): ?><input type="hidden" name="search" value="<?php echo htmlspecialchars($search); ?>"><?php endif; ?>
      <select name="rootfile" class="form-select form-select-sm d-inline-block w-auto" onchange="this.form.submit()">
        <?php foreach ($rootFiles as $rf): ?>
          <option value="<?php echo htmlspecialchars($rf); ?>" <?php if ($rf === $selectedRoot) echo 'selected'; ?>>
            <?php echo htmlspecialchars($rf); ?>
          </option>
        <?php endforeach; ?>
      </select>
    </form>
    <?php else: ?>
    <small class="text-muted fw-normal"><?php echo htmlspecialchars($selectedRoot); ?></small>
    <?php endif; ?>
  </h5>

  <!-- Size controls for ROOT cards -->
  <div class="d-flex align-items-center mb-2 gap-3 flex-wrap">
    <div class="d-flex align-items-center gap-2">
      <label for="rootW" class="mb-0 small">Card width:</label>
      <input type="range" id="rootW" min="200" max="800" value="340" style="width:180px">
      <span id="rootWVal" class="small text-muted">340px</span>
    </div>
    <div class="d-flex align-items-center gap-2">
      <label for="rootH" class="mb-0 small">Plot height:</label>
      <input type="range" id="rootH" min="150" max="600" value="300" style="width:180px">
      <span id="rootHVal" class="small text-muted">300px</span>
    </div>
  </div>

  <div class="d-flex flex-wrap" id="rootGrid">
    <p class="empty-text" id="rootLoading">Opening <strong><?php echo htmlspecialchars($selectedRoot); ?></strong>&hellip;</p>
  </div>
  <?php endif; ?>

  <!-- ── PNG/JPEG/GIF/PDF plot cards (original style) ──────────────────── -->
  <h5 class="mt-4">Plots</h5>
  <div class="d-flex align-items-center mb-2" style="gap:10px;">
    <label for="imgSize" class="mb-0">Image size:</label>
    <input type="range" id="imgSize" min="80" max="400" value="180" style="width:220px">
  </div>
  <div class="d-flex flex-wrap" id="plot-listing">
  <?php
  $displayed      = array();
  $formats        = array('png','pdf','root','C','jpg','jpeg','gif');
  $colorMap       = array('png'=>'primary','pdf'=>'danger','root'=>'dark','c'=>'success',
                          'jpg'=>'warning','jpeg'=>'warning','gif'=>'info');

  foreach ($files as $file) {
      if (!is_plot($file) && !preg_match('/\.(C)$/i', $file)) continue;
      if (!matches_search($file, $search)) continue;

      $base = preg_replace('/\.(png|jpe?g|gif|pdf|root|C)$/i', '', $file);
      if (in_array($base, $displayed)) continue;

      $available = array();
      foreach ($formats as $fmt) {
          $candidate = $base . '.' . $fmt;
          if (file_exists($candidate)) $available[$fmt] = $candidate;
      }

      $thumb = isset($available['png']) ? $available['png'] : null;
      if (!$thumb) continue;

      $displayed[] = $base;
      $baseName    = basename($base);

      echo '<div class="card">';
      echo '<a href="' . htmlspecialchars($thumb) . '" target="_blank">';
      echo '<div class="card-header text-danger fw-bold text-center">' . htmlspecialchars($baseName) . '</div>';
      echo '<img src="' . htmlspecialchars($thumb) . '" class="card-img-top" alt="' . htmlspecialchars($thumb) . '">';
      echo '</a>';
      echo '<div class="card-footer text-center">';
      foreach ($available as $fmt => $path) {
          $col = isset($colorMap[strtolower($fmt)]) ? $colorMap[strtolower($fmt)] : 'secondary';
          echo '<a href="' . htmlspecialchars($path) . '" target="_blank" class="badge bg-' . $col . ' mx-1 text-decoration-none">' . htmlspecialchars($fmt) . '</a>';
      }
      echo '</div></div>';
  }
  if (empty($displayed)) echo "<p class='empty-text'>No plots to display</p>";
  ?>
  </div>

  <!-- ── Standalone images (PNG/JPG not part of a plot group) ─────────── -->
  <?php
  // Only show images NOT already shown as plot thumbnails
  $displayedThumbs = array_map(function($b){ return $b . '.png'; }, $displayed);
  $standaloneImgs  = array_filter($imageFiles, function($f) use ($displayedThumbs) {
      return !in_array($f, $displayedThumbs);
  });
  if (!empty($standaloneImgs)):
  ?>
  <h5 class="mt-4">Images</h5>
  <div class="d-flex flex-wrap" id="imgListing">
    <?php foreach ($standaloneImgs as $f):
      $ext = strtolower(pathinfo($f, PATHINFO_EXTENSION));
      $url = rawurlencode($f);
    ?>
    <div class="card" style="margin:5px;max-width:240px;">
      <div class="card-header text-primary fw-bold text-center" style="font-size:.8rem"><?php echo htmlspecialchars(basename($f)); ?></div>
      <a href="#" onclick="openImgModal('<?php echo addslashes($url); ?>','<?php echo addslashes($f); ?>');return false;">
        <img src="<?php echo $url; ?>" class="card-img-top" alt="<?php echo htmlspecialchars($f); ?>" loading="lazy" style="max-height:180px;object-fit:contain">
      </a>
      <div class="card-footer text-center">
        <a href="<?php echo $url; ?>" target="_blank" class="badge bg-primary mx-1 text-decoration-none">open</a>
        <a href="<?php echo $url; ?>" download class="badge bg-secondary mx-1 text-decoration-none">dl</a>
      </div>
    </div>
    <?php endforeach; ?>
  </div>
  <?php endif; ?>

  <!-- ── PDF files ────────────────────────────────────────────────────── -->
  <?php
  $standalonePdfs = array_filter($pdfFiles, function($f) use ($displayed) {
      $base = preg_replace('/\.pdf$/i', '', $f);
      return !in_array($base, $displayed);
  });
  if (!empty($standalonePdfs)):
  ?>
  <h5 class="mt-4">PDF files</h5>
  <div class="d-flex flex-wrap">
    <?php foreach ($standalonePdfs as $f):
      $url = rawurlencode($f);
    ?>
    <div class="card" style="margin:5px;width:380px;">
      <div class="card-header text-danger fw-bold text-center" style="font-size:.8rem"><?php echo htmlspecialchars(basename($f)); ?></div>
      <iframe class="pdf-embed" src="<?php echo $url; ?>" title="<?php echo htmlspecialchars($f); ?>" loading="lazy"></iframe>
      <div class="card-footer text-center">
        <a href="<?php echo $url; ?>" target="_blank" class="badge bg-danger mx-1 text-decoration-none">open ↗</a>
        <a href="<?php echo $url; ?>" download class="badge bg-secondary mx-1 text-decoration-none">download</a>
      </div>
    </div>
    <?php endforeach; ?>
  </div>
  <?php endif; ?>

  <!-- ── Other files ──────────────────────────────────────────────────── -->
  <h5 class="mt-4">Other files</h5>
  <ul>
  <?php
  $others = array();
  foreach ($files as $f) {
      if (is_plot($f)) continue;
      if (preg_match('/\.(root|C|svg)$/i', $f)) continue;
      if (basename($f) === 'index.php') continue;
      if (!matches_search($f, $search)) continue;
      $others[] = $f;
  }
  if (!empty($others)) {
      foreach ($others as $f)
          echo '<li><a href="' . htmlspecialchars(rawurlencode($f)) . '">' . htmlspecialchars($f) . '</a></li>';
  } else {
      echo "<p class='empty-text'>No files to display</p>";
  }
  ?>
  </ul>

  <div class="text-start mt-3 mb-4">
    <button id="scroll-top" class="btn btn-outline-primary btn-sm">To top</button>
  </div>
</div><!-- /container-fluid -->

<!-- ── JSROOT fullscreen modal ──────────────────────────────────────────── -->
<div class="modal fade" id="rootModal" tabindex="-1" aria-labelledby="rootModalLabel">
  <div class="modal-dialog modal-xl" style="max-width:96vw;margin:2vh auto;">
    <div class="modal-content" style="height:94vh;display:flex;flex-direction:column;">
      <div class="modal-header py-2">
        <h6 class="modal-title mb-0" id="rootModalLabel">Histogram</h6>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body p-0" style="flex:1;overflow:hidden;">
        <div id="rootModalPlot" style="width:100%;height:100%;"></div>
      </div>
    </div>
  </div>
</div>

<!-- ── Image lightbox modal ─────────────────────────────────────────────── -->
<div class="modal fade" id="imgModal" tabindex="-1">
  <div class="modal-dialog modal-xl" style="max-width:92vw;margin:4vh auto;">
    <div class="modal-content">
      <div class="modal-header py-2">
        <h6 class="modal-title mb-0" id="imgModalLabel">Image</h6>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body text-center p-2">
        <img id="imgModalImg" src="" alt="" style="max-width:100%;max-height:82vh;object-fit:contain;">
      </div>
      <div class="modal-footer py-1">
        <a id="imgModalLink" class="btn btn-sm btn-outline-primary" href="#" target="_blank" rel="noopener">Open in new tab ↗</a>
        <a id="imgModalDl"   class="btn btn-sm btn-primary" href="#" download>Download</a>
      </div>
    </div>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>

<script type="module">
import { openFile, draw, cleanup, resize } from 'https://root.cern/js/latest/modules/main.mjs';

// ── JSROOT histogram loading ─────────────────────────────────────────────
var HIST_CLASSES = ['TH1F','TH1D','TH1I','TH1S','TH1C',
                    'TH2F','TH2D','TH2I','TH2S','TH2C',
                    'TH3F','TH3D','TH3I',
                    'TProfile','TProfile2D','TProfile3D'];

function drawOpt(cls) {
  if (cls.indexOf('TH2') === 0 || cls.indexOf('TH3') === 0 ||
      cls === 'TProfile2D' || cls === 'TProfile3D') return 'colz';
  return 'hist';
}
function safeId(name) {
  return 'rp_' + name.replace(/[^a-zA-Z0-9_]/g, '_');
}

var gFile   = null;   // keep file open for re-use in modal
var gObjs   = {};     // cache read objects {keyName -> obj}
var modalBs = null;

<?php if ($selectedRoot): ?>
var ROOT_FILE = '<?php echo addslashes($selectedRoot); ?>';
<?php else: ?>
var ROOT_FILE = null;
<?php endif; ?>

async function loadHistograms() {
  if (!ROOT_FILE) return;
  var grid    = document.getElementById('rootGrid');
  var loading = document.getElementById('rootLoading');
  var countEl = document.getElementById('rootCount');

  try {
    gFile = await openFile(ROOT_FILE);
    var keys     = gFile.fKeys || [];
    var histKeys = keys.filter(function(k){ return HIST_CLASSES.indexOf(k.fClassName) >= 0; });

    if (histKeys.length === 0) {
      loading.textContent = 'No histogram keys found in file.';
      return;
    }
    loading.parentNode.removeChild(loading);
    var h5 = document.querySelector('h5.root-count-h5');
    if (h5) h5.textContent = histKeys.length + ' histograms';

    for (var i = 0; i < histKeys.length; i++) {
      var key   = histKeys[i];
      var name  = key.fName;
      var cycle = key.fCycle || 1;
      var cls   = key.fClassName;
      var title = key.fTitle || name;
      var pid   = safeId(name);

      var card = document.createElement('div');
      card.className = 'card root-card';
      card.dataset.keyname = name;
      card.dataset.cycle   = cycle;
      card.dataset.cls     = cls;
      card.innerHTML =
        '<div class="card-header text-danger fw-bold text-center" ' +
             'onclick="openRootModal(\'' + name.replace(/'/g,"\\'") + '\',' + cycle + ',\'' + cls.replace(/'/g,"\\'") + '\',\'' + title.replace(/'/g,"\\'") + '\')" ' +
             'title="Click to open full screen">' +
          name +
          ' <i class="bi bi-arrows-fullscreen" style="font-size:.7rem;opacity:.5"></i>' +
        '</div>' +
        '<div class="root-plot-wrap">' +
          '<div class="root-plot-div" id="' + pid + '"></div>' +
          '<div class="root-plot-status" id="st_' + pid + '">Loading&hellip;</div>' +
        '</div>';
      grid.appendChild(card);

      // draw inline card (IIFE to capture loop vars)
      (function(n, c, cls2, p) {
        gFile.readObject(n + ';' + c).then(function(obj) {
          gObjs[n] = obj;
          return draw(p, obj, drawOpt(cls2));
        }).then(function() {
          var st = document.getElementById('st_' + p);
          if (st) st.parentNode.removeChild(st);
        }).catch(function(e) {
          var st = document.getElementById('st_' + p);
          if (st) { st.style.pointerEvents = 'none'; st.textContent = '\u26a0 ' + (e.message || e); }
        });
      })(name, cycle, cls, pid);
    }

  } catch(err) {
    loading.textContent = '\u26a0 Cannot open ROOT file: ' + (err.message || err);
  }
}

// ── Fullscreen modal ─────────────────────────────────────────────────────
var pendingModal = null;  // {name, cycle, cls} to draw once modal is shown

window.openRootModal = async function(name, cycle, cls, title) {
  var el = document.getElementById('rootModal');
  if (!modalBs) modalBs = new bootstrap.Modal(el);

  document.getElementById('rootModalLabel').textContent = name + '  [' + cls + ']';

  // cleanup previous drawing before showing new one
  var plotDiv = document.getElementById('rootModalPlot');
  plotDiv.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#888;font-size:.9rem;">Loading&hellip;</div>';

  // Pre-fetch the object so it is ready when the modal finishes opening
  try {
    if (!gObjs[name] && gFile) {
      gObjs[name] = await gFile.readObject(name + ';' + cycle);
    }
  } catch(e) { /* will surface in shown handler */ }

  pendingModal = { name: name, cycle: cycle, cls: cls };
  modalBs.show();
};

// Draw AFTER the modal has fully opened (transition complete) so the div
// has its final pixel dimensions — this is what gives axes + labels.
document.getElementById('rootModal').addEventListener('shown.bs.modal', async function() {
  if (!pendingModal) return;
  var p = pendingModal;
  pendingModal = null;

  var plotDiv = document.getElementById('rootModalPlot');
  // full cleanup of any previous JSROOT painter
  await cleanup(plotDiv);
  plotDiv.innerHTML = '';

  try {
    var obj = gObjs[p.name];
    if (!obj && gFile) {
      obj = await gFile.readObject(p.name + ';' + p.cycle);
      gObjs[p.name] = obj;
    }
    if (obj) {
      // Use explicit size hint matching the modal body dimensions
      var w = plotDiv.clientWidth  || plotDiv.offsetWidth  || 900;
      var h = plotDiv.clientHeight || plotDiv.offsetHeight || 700;
      var opt = drawOpt(p.cls);
      // Pass width/height so JSROOT never guesses 0×0
      await draw('rootModalPlot', obj, opt + ';w=' + w + ';h=' + h);
      // One extra resize call after draw to make sure axes are rendered
      try { resize(plotDiv); } catch(e2) {}
    }
  } catch(e) {
    plotDiv.innerHTML = '<p class="text-danger p-3">' + (e.message || e) + '</p>';
  }
});

// cleanup modal plot when closed
document.getElementById('rootModal').addEventListener('hidden.bs.modal', async function() {
  pendingModal = null;
  await cleanup(document.getElementById('rootModalPlot'));
});

// ── Card size sliders ────────────────────────────────────────────────────
var rootW = document.getElementById('rootW');
var rootH = document.getElementById('rootH');
if (rootW) {
  rootW.addEventListener('input', function() {
    document.documentElement.style.setProperty('--root-card-w', this.value + 'px');
    document.getElementById('rootWVal').textContent = this.value + 'px';
    // resize all visible JSROOT plots
    document.querySelectorAll('.root-plot-div').forEach(function(d) { try { resize(d); } catch(e){} });
  });
}
if (rootH) {
  rootH.addEventListener('input', function() {
    document.documentElement.style.setProperty('--root-card-h', this.value + 'px');
    document.getElementById('rootHVal').textContent = this.value + 'px';
    document.querySelectorAll('.root-plot-div').forEach(function(d) { try { resize(d); } catch(e){} });
  });
}

// ── Image modal ──────────────────────────────────────────────────────────
window.openImgModal = function(url, name) {
  document.getElementById('imgModalImg').src   = url;
  document.getElementById('imgModalImg').alt   = name;
  document.getElementById('imgModalLink').href = url;
  document.getElementById('imgModalDl').href   = url;
  document.getElementById('imgModalDl').download = name;
  document.getElementById('imgModalLabel').textContent = name;
  new bootstrap.Modal(document.getElementById('imgModal')).show();
};

// ── PNG size slider ──────────────────────────────────────────────────────
var imgSizeSlider = document.getElementById('imgSize');
if (imgSizeSlider) {
  imgSizeSlider.addEventListener('input', function() {
    document.documentElement.style.setProperty('--plot-img-max-height', this.value + 'px');
  });
  document.documentElement.style.setProperty('--plot-img-max-height', imgSizeSlider.value + 'px');
}

// ── Scroll to top ────────────────────────────────────────────────────────
document.getElementById('scroll-top').onclick = function() {
  window.scrollTo({top: 0, behavior: 'smooth'});
};

// ── Boot ─────────────────────────────────────────────────────────────────
loadHistograms();
</script>
</body>
</html>
